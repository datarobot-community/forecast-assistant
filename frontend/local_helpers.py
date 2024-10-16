# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from __future__ import annotations

import json
import sys
from typing import Tuple

import datarobot as dr
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from pydantic import ValidationError

sys.path.append("../")
from forecastic.predict import get_completion, make_datarobot_predictions
from forecastic.schema import AppSettings, DynamicAppSettings
from forecastic.settings_app import static_app_settings

try:
    with open("dynamic_app_settings.json") as f:
        dynamic_app_settings = DynamicAppSettings.model_validate(json.load(f))
        app_settings = AppSettings(
            **dynamic_app_settings.model_dump(), **static_app_settings.model_dump()
        )
except ValidationError as e:
    print(e)
    raise ValueError(
        (
            "Unable to read App settings. If running locally, verify you have selected "
            "the correct stack and that it is active using `pulumi stack output`. "
            "If running in DataRobot, verify your runtime parameters have been set correctly."
        )
    ) from e


@st.cache_data(show_spinner=False)
def get_scoring_data(dataset_id: str) -> pd.DataFrame:
    """Get the scoring data from DataRobot"""
    return dr.Dataset.get(dataset_id).get_as_dataframe()  # type: ignore[attr-defined]


@st.cache_data(show_spinner=False)
def process_predictions(
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    prediction_interval = f"{app_settings.prediction_interval:.0f}"
    bound_at_zero = app_settings.lower_bound_forecast_at_0

    data = predictions
    target = dr.Project.get(app_settings.project_id).target  # type: ignore[attr-defined]

    series_id = app_settings.datetime_partition_column
    target = f"{target}_PREDICTION"
    slim_predictions = data[
        [series_id, "FORECAST_POINT", target]
        + [c for c in data.columns if "EXPLANATION" in c]
    ]

    percentile_prefix = f"PREDICTION_{prediction_interval}_PERCENTILE"

    intervals = data[[c for c in data.columns if percentile_prefix in c]]

    clean_predictions = pd.concat([slim_predictions, intervals], axis=1)

    clean_predictions = clean_predictions.rename(
        columns={
            target: "prediction",
            f"{percentile_prefix}_LOW": "low",
            f"{percentile_prefix}_HIGH": "high",
        }
    )
    # st.write(data)
    if bound_at_zero:
        bounds = ["prediction", "low", "high"]
        clean_predictions[bounds] = clean_predictions[bounds].clip(lower=0)

    return clean_predictions


@st.cache_data(show_spinner=False)
def get_prompt(
    prediction_explanations_df: pd.DataFrame,
    target: str,
    ex_target: bool = False,
    use_ranks: bool = True,
    top_feature_threshold: int = 75,
    top_n_features: int = 4,
) -> str:
    """Build prompt to summarize pred explanations data."""
    total_strength = (
        prediction_explanations_df.groupby("feature")["strength"]
        .apply(lambda c: c.abs().sum())
        .sort_values(ascending=False)
    )
    total_strength = ((total_strength / total_strength.sum()) * 100).astype(int)
    total_strength.name = "Relative importance (%)"
    total_strength.index.name = None
    cum_total_strength = total_strength.cumsum()
    if use_ranks:
        total_strength = pd.Series(
            range(1, 1 + len(total_strength)), index=total_strength.index
        )
        total_strength.name = "Rank"
    top_features = pd.DataFrame(
        total_strength[cum_total_strength.shift(1).fillna(0) < top_feature_threshold][
            :top_n_features
        ]
    ).to_string()
    if not ex_target:
        prompt = (
            "The following are the most important features in the "
            + "forecasting model's predictions. Provide a 3-4 sentence "
            + "summary of the key cyclical and/or trend drivers for the "
            + "forecast, explain any potential intuitive,qualitative "
            + "interpretations or explanations."
        )
    else:
        prompt = (
            "The following are the most important exogenous features "
            + f"in the forecasting model's predictions of `{target}`. "
            + "Provide a 3-4 sentence summary of the exogenous "
            + "driver(s) for the forecast, explain any potential "
            + "intuitive, qualitative interpretation(s) "
            + "or explanation(s)."
        )
    return prompt + f"\n\n\n{top_features}"


def get_tldr(
    preds: pd.DataFrame,
    target: str,
    temperature: float = 0,
) -> Tuple[str, pd.DataFrame]:
    """Get a natural langauge tldr of what the pred expls say about a TS forecast."""
    df = preds
    target_df = df[[c for c in df.columns if "EXPLANATION" in c]]

    names = []
    strengths = []
    values = []

    # Iterate through the columns
    for i in range(1, 4):  # 1, 2, 3
        names.extend(df[f"EXPLANATION_{i}_FEATURE_NAME"])
        strengths.extend(df[f"EXPLANATION_{i}_STRENGTH"])
        values.extend(df[f"EXPLANATION_{i}_ACTUAL_VALUE"])

    # Create the new dataframe
    pred_ex_df = pd.DataFrame(
        {"feature": names, "strength": strengths, "value": values}
    )

    target_df = pred_ex_df[pred_ex_df["feature"].str.startswith(target + " (")].copy()

    target_prompt = get_prompt(target_df, target, ex_target=False)
    target_completion = get_completion(target_prompt, temperature=temperature)
    ex_target_df = pred_ex_df[
        ~pred_ex_df["feature"].str.startswith(target + " (")
    ].copy()

    ex_target_prompt = get_prompt(ex_target_df, target, ex_target=True)
    ex_target_completion = get_completion(ex_target_prompt, temperature=temperature)
    explain_df = pd.concat((target_df, ex_target_df)).reset_index(drop=True)
    return target_completion + "\n\n\n" + ex_target_completion, explain_df


@st.cache_data(show_spinner=False)
def create_chart(
    history: pd.DataFrame,
    forecast: pd.DataFrame,
    title: str,
) -> go.Figure:
    datetime_partition_column = app_settings.datetime_partition_column
    target = app_settings.target
    date_format = app_settings.date_format
    fig = make_subplots(specs=[[{"secondary_y": False}]])

    history = history.copy().assign(
        timestamp=pd.to_datetime(history[datetime_partition_column], format=date_format)
    )

    fig.add_trace(
        go.Scatter(
            x=history.timestamp,
            y=history[target],
            mode="lines",
            name=f"{target} History",
            line_shape="spline",
            line=dict(color="#ff9e00", width=2),
        )
    )
    # st.write(forecast)
    fig.add_trace(
        go.Scatter(
            x=forecast[datetime_partition_column],
            y=forecast["low"],
            mode="lines",
            name="Low forecast",
            line_shape="spline",
            line=dict(color="#335599", width=0.5, dash="dot"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast[datetime_partition_column],
            y=forecast["high"],
            mode="lines",
            name="High forecast",
            line_shape="spline",
            line=dict(color="#335599", width=0.5, dash="dot"),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast[datetime_partition_column],
            y=forecast["prediction"],
            mode="lines",
            name=f"Total {target} Forecast",
            line_shape="spline",
            line=dict(color="#162955", width=2),
        )
    )

    fig.add_vline(
        x=history.loc[lambda x: ~pd.isna(x[target]), "timestamp"].max(),
        line_width=2,
        line_dash="dash",
        line_color="gray",
    )

    fig.update_xaxes(
        color="#404040",
        title_font_family="Gravitas One",
        title_text=datetime_partition_column,
        linecolor="#adadad",
    )

    fig.update_yaxes(
        color="#404040",
        title_font_size=16,
        title_text=app_settings.graph_y_axis,
        linecolor="#adadad",
        gridcolor="#f2f2f2",
    )

    fig.update_layout(
        height=600,
        title=title,
        title_font_size=20,
        hovermode="x unified",
        plot_bgcolor="#ffffff",
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.5),
        margin=dict(l=50, r=50, b=20, t=50, pad=4),
        xaxis=dict(rangeslider=dict(visible=True), type="date"),
        uniformtext_mode="hide",
    )

    fig.update_layout(xaxis=dict(fixedrange=False), yaxis=dict(fixedrange=False))
    fig.update_traces(connectgaps=False)

    return fig


@st.cache_data(show_spinner=False)
def scoreForecast(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Make and format predictions

    Returns
    -------
    tuple(pd.DataFrame, pd.DataFrame)
        DataFrame of predictions and processed predictions
    """
    predictions = make_datarobot_predictions(df)
    processed_predictions = process_predictions(predictions)
    return predictions, processed_predictions


def interpretChartHeadline(forecast: pd.DataFrame) -> str:
    return get_completion(
        prompt="Forecast:"
        + str(forecast[[app_settings.datetime_partition_column, "prediction"]]),
        system_prompt=app_settings.headline_prompt,
        temperature=0.2,
    )
