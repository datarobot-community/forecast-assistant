# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from __future__ import annotations

import functools
import json
import subprocess
import sys
from typing import Any, List, Optional

import datarobot as dr
import pandas as pd
import plotly.graph_objects as go
import yaml
from datarobot_predict.deployment import predict
from openai import AzureOpenAI
from plotly.subplots import make_subplots
from pydantic import ValidationError

sys.path.append("..")

from forecastic.credentials import AzureOpenAICredentials
from forecastic.resources import ScoringDataset, TimeSeriesDeployment
from forecastic.schema import (
    AppSettings,
    FilterSpec,
    ForecastSummary,
    MultiSelectFilter,
    PredictionRow,
)


def get_stack_suffix() -> str:
    try:
        return (
            "."
            + subprocess.check_output(
                ["pulumi", "stack", "--show-name", "--non-interactive"],
                text=True,
                stderr=subprocess.STDOUT,
            ).strip()
        )
    except Exception:
        pass
    return ""


app_settings_file_name = f"train_model_output{get_stack_suffix()}.yaml"
try:
    with open(app_settings_file_name) as f:
        app_settings = AppSettings(**yaml.safe_load(f))

    time_series_deployment_id = TimeSeriesDeployment().id
    scoring_dataset_id = ScoringDataset().id
    credentials = AzureOpenAICredentials()
    azure_client = AzureOpenAI(
        azure_endpoint=credentials.azure_endpoint,
        api_key=credentials.api_key,
        api_version=credentials.api_version,
    )
except (FileNotFoundError, ValidationError) as e:
    raise ValueError(
        (
            "Unable to load Deployment IDs or Application Settings. "
            "If running locally, verify you have selected the correct "
            "stack and that it is active using `pulumi stack output`. "
            "If running in DataRobot, verify your runtime parameters have been set correctly."
        )
    ) from e


def get_app_settings() -> AppSettings:
    return app_settings


@functools.lru_cache(maxsize=16)
def _get_scoring_data() -> pd.DataFrame:
    """Get the scoring data from DataRobot."""
    return dr.Dataset.get(scoring_dataset_id).get_as_dataframe()  # type: ignore[attr-defined]


def get_scoring_data(
    filter_selection: Optional[List[FilterSpec]] = None,
) -> list[dict[str, Any]]:
    """
    Get scoring data from DataRobot.

    Scoring data will be filtered based on the selected filters.
    An exception will be raised if no data is available for the selected series.

    Parameters
    ----------
    filter_selection : Optional[List[FilterSpec]]
        List of filters to apply to the data.
    """
    df = _get_scoring_data()
    if filter_selection is None:
        return df.to_dict(orient="records")  # type: ignore[no-any-return]
    for widget in filter_selection:
        widget_values = widget.selected_values
        column_name = widget.column
        if len(widget_values) > 0:
            df = df[df[column_name].isin(widget_values)]
    if len(df) == 0:
        raise ValueError(
            "No data available for the selected series. Try a different combination of filters."
        )
    return df.to_dict(orient="records")  # type: ignore[no-any-return]


def get_filters() -> List[MultiSelectFilter]:
    """
    Get available options for each filter.

    Returns
    -------
    List[MultiSelectFilter]
        Available filters and displays.
    """

    scoring_data = _get_scoring_data()
    filters = []
    for category in app_settings.filterable_categories:
        filters.append(
            MultiSelectFilter(
                column_name=category.column_name,
                display_name=category.display_name,
                valid_values=scoring_data[category.column_name].unique().tolist(),
            )
        )
    return filters


def get_predictions(scoring_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Retrieve predictions in the format returned by DataRobot-Predict.

    Parameters
    ----------
    data : list[dict]
        A list of dictionaries containing the input data for generating predictions.

    Returns
    -------
    list[dict[str, Any]]
        List of predictions from deployed time series model.
    """

    predictions = _get_predictions_cached(json.dumps(scoring_data, sort_keys=True))

    return predictions.to_dict(orient="records")  # type: ignore[no-any-return]


@functools.lru_cache(maxsize=16)
def _get_predictions_cached(scoring_data_json: str) -> pd.DataFrame:
    predictions = predict(
        deployment=dr.Deployment.get(time_series_deployment_id),  # type: ignore[attr-defined]
        data_frame=pd.DataFrame(json.loads(scoring_data_json)),
        max_explanations=3,
    ).dataframe

    return predictions


def get_standardized_predictions(
    scoring_data: list[dict[str, Any]],
) -> list[PredictionRow]:
    """Retreive predictions and process them into a standardized format.

    Format cast is independent of the scoring data.

    Parameters
    ----------
    data : list[dict]
        A list of dictionaries containing the input data for generating predictions.

    Returns
    -------
    list[PredictionRow]
        A list of PredictionRow objects representing the processed and standardized predictions.
    """
    predictions = get_predictions(scoring_data)
    processed_predictions = _process_predictions(predictions)

    return processed_predictions


def _process_predictions(predictions: list[dict[str, Any]]) -> list[PredictionRow]:
    """Translate predictions into standardized format."""

    data = pd.DataFrame(predictions)

    prediction_interval = f"{app_settings.prediction_interval:.0f}"
    bound_at_zero = app_settings.lower_bound_forecast_at_0

    target = dr.Project.get(app_settings.project_id).target  # type: ignore[attr-defined]

    date_id = app_settings.datetime_partition_column
    series_id = app_settings.multiseries_id_column
    target = f"{target}_PREDICTION"
    slim_predictions = data[[series_id, date_id, target]].rename(
        columns={date_id: "date_id"}
    )

    percentile_prefix = f"PREDICTION_{prediction_interval}_PERCENTILE"

    intervals = data[[c for c in data.columns if percentile_prefix in c]]

    clean_predictions = pd.concat([slim_predictions, intervals], axis=1)

    clean_predictions = (
        clean_predictions.rename(
            columns={
                target: "prediction",
                f"{percentile_prefix}_LOW": "low",
                f"{percentile_prefix}_HIGH": "high",
            }
        )
        .groupby("date_id")
        .sum()
        .reset_index()
    )
    if bound_at_zero:
        bounds = ["prediction", "low", "high"]
        clean_predictions[bounds] = clean_predictions[bounds].clip(lower=0)
    return [PredictionRow(**i) for i in clean_predictions.to_dict(orient="records")]


def get_forecast_as_plotly_json(
    scoring_data: list[dict[str, Any]], n_historical_records_to_display: int
) -> dict[str, Any]:
    """
    Render the forecast chart as a Plotly figure.

    This function takes historical and forecasted data, processes it,
    and generates a Plotly figure representing the historical data and
    forecasted predictions. The figure includes lines for the
    historical data, low and high forecast bounds, and the predicted forecast.

    Parameters
    ----------
    scoring_data : list[dict[str, Any]]
        A list of dictionaries containing the input data for generating predictions.
    n_historical_records_to_display : int
        The number of historical records to display in the chart

    Returns
    -------
    dict[str, Any]
        A dictionary representation of the plotly figure.
    """

    datetime_partition_column = app_settings.datetime_partition_column
    target = app_settings.target

    forecast = pd.DataFrame(
        [i.model_dump() for i in get_standardized_predictions(scoring_data)]
    )
    history = _aggregate_scoring_data(scoring_data).tail(
        n_historical_records_to_display
    )

    fig = make_subplots(specs=[[{"secondary_y": False}]])

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
    fig.add_trace(
        go.Scatter(
            x=forecast["date_id"],
            y=forecast["low"],
            mode="lines",
            name="Low forecast",
            line_shape="spline",
            line=dict(color="#63b6f9", width=0.5, dash="dot"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["date_id"],
            y=forecast["high"],
            mode="lines",
            name="High forecast",
            line_shape="spline",
            line=dict(color="#63b6f9", width=0.5, dash="dot"),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast["date_id"],
            y=forecast["prediction"],
            mode="lines",
            name=f"Total {target} Forecast",
            line_shape="spline",
            line=dict(color="#63b6f9", width=2),
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
        showgrid=False,
        linecolor="#adadad",
    )

    fig.update_yaxes(
        color="#404040",
        title_font_size=16,
        title_text=app_settings.graph_y_axis,
        linecolor="#adadad",
    )

    fig.update_layout(
        height=600,
        hovermode="x unified",
        plot_bgcolor="#474747",
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.5),
        margin=dict(l=50, r=50, b=20, t=50, pad=4),
        xaxis=dict(rangeslider=dict(visible=True), type="date"),
        title="",
        uniformtext_mode="hide",
    )

    fig.update_layout(xaxis=dict(fixedrange=False), yaxis=dict(fixedrange=False))
    fig.update_traces(connectgaps=False)

    return fig.to_dict()  # type: ignore[no-any-return]


def _aggregate_scoring_data(scoring_data: list[dict[str, Any]]) -> pd.DataFrame:
    """Aggregate scoring data for plotting."""
    datetime_column = app_settings.datetime_partition_column
    date_format = app_settings.date_format

    return (
        pd.DataFrame(scoring_data)
        .groupby(datetime_column, dropna=True)
        .sum(min_count=1)
        .reset_index()
        .assign(
            timestamp=lambda x: pd.to_datetime(x[datetime_column], format=date_format)
        )
    )


def get_llm_summary(predictions: List[dict[str, Any]]) -> ForecastSummary:
    """
    Generate summary and headline of the forecast from the LLM model.

    Processes a list of prediction dictionaries, extracts relevant
    features, strengths, and values, and then generates a summary and headline
    using a language model. It also creates an explanation dataset.

    Parameters
    ----------
    predictions : List[dict[str, Any]]
        A list of dictionaries containing prediction data. Each dictionary should
        have keys corresponding to feature names, strengths, and actual values.

    Returns
    -------
    ForecastSummary
        An object containing the headline, summary body, and explanation dataset.
    """

    preds = pd.DataFrame(predictions)
    processed_preds = _process_predictions(predictions)

    names = []
    strengths = []
    values = []

    for i in range(1, 4):  # 1, 2, 3
        names.extend(preds[f"EXPLANATION_{i}_FEATURE_NAME"])
        strengths.extend(preds[f"EXPLANATION_{i}_STRENGTH"])
        values.extend(preds[f"EXPLANATION_{i}_ACTUAL_VALUE"])

    pred_ex_df = pd.DataFrame(
        {"feature": names, "strength": strengths, "value": values}
    )

    # Create summary for target derived features
    include_target_prompt_df, include_target_summary = _summarize_dataframe(
        pred_ex_df, ex_target=False
    )

    # Create summary for exogenous features
    exclude_target_prompt_df, exclude_target_summary = _summarize_dataframe(
        pred_ex_df, ex_target=True
    )
    explain_df = pd.concat((include_target_prompt_df, exclude_target_prompt_df)).rename(
        columns={
            "Relative Importance": "relative_importance",
            "index": "feature_name",
        }
    )

    return ForecastSummary(
        headline=_make_headline(processed_preds),
        summary_body=include_target_summary + "\n\n\n" + exclude_target_summary,
        feature_explanations=explain_df.to_dict(orient="records"),
    )


def _summarize_dataframe(
    prompt_dataframe: pd.DataFrame, ex_target: bool
) -> tuple[pd.DataFrame, str]:
    """
    Get the LLM sub-summary for the forecast.
    """
    target = app_settings.target
    if ex_target:
        prompt = (
            "The following are the most important exogenous features "
            + f"in the forecasting model's predictions of `{target}`. "
            + "Provide a 3-4 sentence summary of the exogenous "
            + "driver(s) for the forecast, explain any potential "
            + "intuitive, qualitative interpretation(s) "
            + "or explanation(s)."
        )
        explain_df = prompt_dataframe[
            ~prompt_dataframe["feature"].str.startswith(target + " (")
        ].copy()
    else:
        prompt = (
            "The following are the most important features in the "
            + "forecasting model's predictions. Provide a 3-4 sentence "
            + "summary of the key cyclical and/or trend drivers for the "
            + "forecast, explain any potential intuitive,qualitative "
            + "interpretations or explanations."
        )
        explain_df = prompt_dataframe[
            prompt_dataframe["feature"].str.startswith(target + " (")
        ].copy()
    prompt_string, prompt_df = _get_prompt(
        explain_df,
        prompt,
    )
    prompt_completion = _get_completion(prompt_string, temperature=0)
    return (
        prompt_df.assign(is_target_derived=ex_target).reset_index(),
        prompt_completion,
    )


def _get_prompt(
    prediction_explanations_df: pd.DataFrame,
    prompt: str,
    top_feature_threshold: int = 75,
    top_n_features: int = 4,
) -> tuple[str, pd.DataFrame]:
    """Build prompt to summarize prediction explanations data."""
    total_strength = (
        prediction_explanations_df.groupby("feature")["strength"]
        .apply(lambda c: c.abs().sum())
        .sort_values(ascending=False)
    )
    total_strength = ((total_strength / total_strength.sum()) * 100).astype(int)
    total_strength.index.name = None
    cum_total_strength = total_strength.cumsum()
    top_features = pd.DataFrame(
        total_strength[cum_total_strength.shift(1).fillna(0) < top_feature_threshold][
            :top_n_features
        ],
    ).rename(columns={"strength": "relative_importance"})
    top_features["Rank"] = range(1, 1 + len(top_features))

    top_features_string = top_features.drop(columns="relative_importance").to_string()

    return prompt + f"\n\n\n{top_features_string}", top_features.drop(columns="Rank")


def _make_headline(standardized_predictions: list[PredictionRow]) -> str:
    """Generate subheader for explanation."""
    df = pd.DataFrame([i.model_dump() for i in standardized_predictions])
    return _get_completion(
        prompt="Forecast:" + str(df[["date_id", "prediction"]]),
        system_prompt=app_settings.headline_prompt,
        temperature=0.2,
    )


def _get_completion(
    prompt: str,
    temperature: float = 0,
    system_prompt: Optional[str] = None,
    llm_model_name: Optional[str] = None,
) -> str:
    """Generate LLM completion."""
    if system_prompt:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
    else:
        messages = [{"role": "user", "content": prompt}]
    resp = azure_client.chat.completions.create(
        messages=messages,  # type: ignore[arg-type]
        model=(
            llm_model_name
            if llm_model_name is not None
            else credentials.azure_deployment
        ),
        temperature=temperature,
    )
    return str(resp.choices[0].message.content)


def share_access(emails: List[str]) -> tuple[str, int]:
    """Share application with other users."""
    client = dr.Client()  # type: ignore[attr-defined]
    application_name = app_settings.application_name.replace(" ", "%20")  # type: ignore[attr-defined]

    try:
        url = f"customApplications/?name={application_name}"
        application_id = client.get(url).json()["data"][0]["id"]
        url = f"customApplications/{application_id}/sharedRoles"
        roles = [
            {"role": "CONSUMER", "shareRecipientType": "user", "username": email}
            for email in emails
        ]
        payload = {"operation": "updateRoles", "roles": roles}
        client.patch(url, json=payload)
        return "Success", 200
    except Exception as e:
        return str(e), 500
