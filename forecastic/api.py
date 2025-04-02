# Copyright 2024 DataRobot, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import annotations

import datetime as dt
import functools
import json
import sys
from importlib import resources
from typing import Any, List, Optional, Tuple
from urllib.parse import urljoin

import datarobot as dr
import pandas as pd
import plotly.graph_objects as go
import yaml
from datarobot.errors import ClientError
from datarobot_predict.deployment import predict
from openai import OpenAI
from plotly.subplots import make_subplots
from pydantic import ValidationError

sys.path.append("..")

from forecastic.i18n import gettext
from forecastic.resources import (
    Application,
    GenerativeDeployment,
    ScoringDataset,
    TimeSeriesDeployment,
    app_settings_file_name,
)
from forecastic.schema import (
    AppRuntimeAttributes,
    AppSettings,
    AppUrls,
    FilterSpec,
    ForecastSummary,
    MultiSelectFilter,
    PredictionRow,
)

try:
    # Load static settings w/o making assumptions about working directory
    app_settings = AppSettings(
        **yaml.safe_load(
            resources.files(__name__.split(".")[0])
            .joinpath(app_settings_file_name)
            .read_text()
        )
    )

    time_series_deployment_id = TimeSeriesDeployment().id
    scoring_dataset_id = ScoringDataset().id

except (FileNotFoundError, ValidationError) as e:
    raise ValueError(
        gettext(
            "Unable to load Deployment IDs or Application Settings. "
            "If running locally, verify you have selected the correct "
            "stack and that it is active using `pulumi stack output`. "
            "If running in DataRobot, verify your runtime parameters have been set correctly."
        )
    ) from e


class LLMNotAvailableException(Exception):
    """Exception raised when the LLM is unavailable."""


def _get_completion(
    prompt: str,
    temperature: float = 0,
    system_prompt: Optional[str] = None,
    llm_model_name: Optional[str] = None,
) -> str:
    """Generate LLM completion."""
    generative_deployment_id = GenerativeDeployment().id
    try:
        dr_client = dr.client.get_client()
        azure_client = OpenAI(
            base_url=dr_client.endpoint.rstrip("/")
            + f"/deployments/{generative_deployment_id}",
            api_key=dr_client.token,
        )
        if system_prompt:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
        else:
            messages = [{"role": "user", "content": prompt}]
        resp = azure_client.chat.completions.create(
            messages=messages,  # type: ignore[arg-type]
            model="datarobot-deployed-llm",
            temperature=temperature,
        )
        return str(resp.choices[0].message.content)
    except Exception as e:
        raise LLMNotAvailableException("LLM is unavailable.") from e


def get_app_settings() -> AppSettings:
    return app_settings


def _get_app_urls() -> AppUrls:
    base_url = urljoin(dr.Client().endpoint, "..")
    dataset_url = (
        f"usecases/{app_settings.use_case_id}/explore/dataset/{scoring_dataset_id}"
    )
    model_url = f"usecases/{app_settings.use_case_id}/model/leaderboard/{app_settings.project_id}/{app_settings.model_id}"
    deployment_url = f"console-nextgen/deployments/{time_series_deployment_id}/overview"
    return AppUrls(
        dataset=urljoin(base_url, dataset_url),
        model=urljoin(base_url, model_url),
        deployment=urljoin(base_url, deployment_url),
    )


def _get_app_metadata() -> Tuple[str, str]:
    client = dr.Client()
    try:
        application_id = Application().id
        url = f"customApplications/{application_id}/"
        resp = client.get(url).json()
        app_creator_email = resp["createdBy"]
        # Parse "2024-12-10 15:18:53.868000" into date
        app_latest_created_date = dt.datetime.strptime(
            resp["updatedAt"], "%Y-%m-%d %H:%M:%S.%f"
        ).strftime("%Y-%m-%d %H:%M:%S")
    except (ValidationError, ClientError):
        url = "account/info/"
        resp = client.get(url).json()
        app_creator_email = resp["email"]
        app_latest_created_date = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return app_creator_email, app_latest_created_date


def get_runtime_attributes() -> AppRuntimeAttributes:
    """Get relevant urls and application metadata."""
    app_urls = _get_app_urls()
    app_creator_email, app_latest_created_date = _get_app_metadata()

    return AppRuntimeAttributes(
        app_urls=app_urls,
        app_creator_email=app_creator_email,
        app_latest_created_date=app_latest_created_date,
    )


@functools.lru_cache(maxsize=16)
def _get_scoring_data() -> pd.DataFrame:
    """Get the scoring data from DataRobot."""
    return dr.Dataset.get(scoring_dataset_id).get_as_dataframe()


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
            gettext(
                "No data available for the selected series. Try a different combination of filters."
            )
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
    scoring_data : list[dict]
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
        deployment=dr.Deployment.get(time_series_deployment_id),
        data_frame=pd.DataFrame(json.loads(scoring_data_json)),
        max_explanations=3,
    ).dataframe

    return predictions


def get_standardized_predictions(
    scoring_data: list[dict[str, Any]],
) -> list[PredictionRow]:
    """Retrieve predictions and process them into a standardized format.

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

    target = dr.Project.get(app_settings.project_id).target

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


def get_formatted_predictions(
    scoring_data: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Format predictions for the frontend."""
    predictions = get_predictions(scoring_data)
    formatted_predictions = _format_predictions(predictions)

    return formatted_predictions


def _format_predictions(predictions: list[dict[str, Any]]) -> list[dict[Any, Any]]:
    """Format predictions for the frontend."""

    data = pd.DataFrame(predictions)

    target = dr.Project.get(app_settings.project_id).target
    multiseries_id_column = app_settings.multiseries_id_column
    date_id = app_settings.datetime_partition_column
    prediction_interval = f"{app_settings.prediction_interval:.0f}"
    percentile_prefix = f"PREDICTION_{prediction_interval}_PERCENTILE"

    data["timestamp"] = data[date_id]
    data["prediction"] = data[f"{target}_PREDICTION"]
    data["seriesId"] = data[multiseries_id_column]
    data["forecastDistance"] = data["FORECAST_DISTANCE"]
    data["forecastPoint"] = data["FORECAST_POINT"]

    data["predictionIntervals"] = data.apply(
        lambda x: {
            prediction_interval: {
                "low": x[f"{percentile_prefix}_LOW"],
                "high": x[f"{percentile_prefix}_HIGH"],
            }
        },
        axis=1,
    )

    data["predictionExplanations"] = data.apply(
        lambda x: [
            {
                "feature": x[f"EXPLANATION_{i}_FEATURE_NAME"],
                "featureValue": x[f"EXPLANATION_{i}_ACTUAL_VALUE"],
                "label": target,
                "qualitativeStrength": x[f"EXPLANATION_{i}_QUALITATIVE_STRENGTH"],
                "strength": x[f"EXPLANATION_{i}_STRENGTH"],
            }
            for i in range(1, len(x.index))
            if f"EXPLANATION_{i}_FEATURE_NAME" in x.index
        ],
        axis=1,
    )

    return data.to_dict(orient="records")  # type: ignore[no-any-return]


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
            name=gettext("{target} History").format(target=target),
            line_shape="spline",
            line=dict(color="#ff9e00", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["date_id"],
            y=forecast["low"],
            mode="lines",
            name=gettext("Low forecast"),
            line_shape="spline",
            line=dict(color="#63b6f9", width=0.5, dash="dot"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["date_id"],
            y=forecast["high"],
            mode="lines",
            name=gettext("High forecast"),
            line_shape="spline",
            line=dict(color="#63b6f9", width=0.5, dash="dot"),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast["date_id"],
            y=forecast["prediction"],
            mode="lines",
            name=gettext("Total {target} Forecast").format(target=target),
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


def get_pred_ex_df(preds: List[dict[str, Any]]) -> pd.DataFrame:
    preds_df = pd.DataFrame(preds)
    names = []
    strengths = []
    values = []

    for i in range(1, 4):  # 1, 2, 3
        names.extend(preds_df[f"EXPLANATION_{i}_FEATURE_NAME"])
        strengths.extend(preds_df[f"EXPLANATION_{i}_STRENGTH"])
        values.extend(preds_df[f"EXPLANATION_{i}_ACTUAL_VALUE"])

    pred_ex_df = pd.DataFrame(
        {"feature": names, "strength": strengths, "value": values}
    )
    return pred_ex_df


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

    # preds = pd.DataFrame(predictions)
    processed_preds = _process_predictions(predictions)
    pred_ex_df = get_pred_ex_df(predictions)

    # Create summary for target derived features
    include_target_summary = _summarize_dataframe(pred_ex_df, ex_target=False)

    # Create summary for exogenous features
    exclude_target_summary = _summarize_dataframe(pred_ex_df, ex_target=True)

    return ForecastSummary(
        headline=_make_headline(processed_preds),
        summary_body=include_target_summary + "\n\n\n" + exclude_target_summary,
    )


def get_explain_df(predictions: List[dict[str, Any]]) -> pd.DataFrame:
    pred_ex_df = get_pred_ex_df(predictions)
    include_target_prompt_df = assemble_prediction_explanations(
        pred_ex_df, ex_target=False
    )
    exclude_target_prompt_df = assemble_prediction_explanations(
        pred_ex_df, ex_target=True
    )

    explain_df = pd.concat((include_target_prompt_df, exclude_target_prompt_df)).rename(
        columns={
            "Relative Importance": "relative_importance",
            "index": "feature_name",
        }
    )
    explain_df = explain_df.sort_values(
        "relative_importance", ascending=False
    ).reset_index(drop=True)
    explain_df["Rank"] = range(1, len(explain_df) + 1)

    return explain_df


def assemble_prediction_explanations(
    explain_df: pd.DataFrame, ex_target: bool
) -> pd.DataFrame:
    target = app_settings.target
    if ex_target:
        explain_df = explain_df[
            ~explain_df["feature"].str.startswith(target + " (")
        ].copy()
    else:
        explain_df = explain_df[
            explain_df["feature"].str.startswith(target + " (")
        ].copy()
    prompt_df = get_top_features(explain_df)
    return prompt_df.assign(is_target_derived=not ex_target).reset_index()


def get_top_features(
    prediction_explanations_df: pd.DataFrame,
    top_feature_threshold: int = 75,
    top_n_features: int = 4,
) -> pd.DataFrame:
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

    return top_features


def _summarize_dataframe(prompt_dataframe: pd.DataFrame, ex_target: bool) -> str:
    """
    Get the LLM sub-summary for the forecast.
    """
    target = app_settings.target
    if ex_target:
        prompt = gettext(
            "The following are the most important exogenous features "
            + "in the forecasting model's predictions of `{target}`. "
            + "Provide a 3-4 sentence summary of the exogenous "
            + "driver(s) for the forecast, explain any potential "
            + "intuitive, qualitative interpretation(s) "
            + "or explanation(s)."
        ).format(target=target)
        explain_df = prompt_dataframe[
            ~prompt_dataframe["feature"].str.startswith(target + " (")
        ].copy()
    else:
        prompt = gettext(
            "The following are the most important features in the "
            + "forecasting model's predictions. Provide a 3-4 sentence "
            + "summary of the key cyclical and/or trend drivers for the "
            + "forecast, explain any potential intuitive,qualitative "
            + "interpretations or explanations."
        )
        explain_df = prompt_dataframe[
            prompt_dataframe["feature"].str.startswith(target + " (")
        ].copy()
    prompt_string = _get_prompt(
        explain_df,
        prompt,
    )
    prompt_completion = _get_completion(prompt_string, temperature=0)
    return prompt_completion


def _get_prompt(
    prediction_explanations_df: pd.DataFrame,
    prompt: str,
) -> str:
    """Build prompt to summarize prediction explanations data."""
    top_features = get_top_features(
        prediction_explanations_df=prediction_explanations_df
    )
    top_features_string = top_features.drop(columns="relative_importance").to_string()

    return prompt + f"\n\n\n{top_features_string}"


def _make_headline(standardized_predictions: list[PredictionRow]) -> str:
    """Generate subheader for explanation."""
    df = pd.DataFrame([i.model_dump() for i in standardized_predictions])
    return _get_completion(
        prompt=gettext("Forecast:") + str(df[["date_id", "prediction"]]),
        system_prompt=app_settings.headline_prompt,
        temperature=0.2,
    )


def share_access(emails: List[str]) -> None:
    """Share application with other users."""
    client = dr.Client()
    try:
        application_id = Application().id
    except ValidationError as e:
        raise ValidationError(
            "Application ID not found. Have you deployed it with pulumi up?"
        ) from e
    url = f"customApplications/{application_id}/sharedRoles"
    roles = [
        {"role": "CONSUMER", "shareRecipientType": "user", "username": email}
        for email in emails
    ]
    payload = {"operation": "updateRoles", "roles": roles}
    client.patch(url, json=payload)
