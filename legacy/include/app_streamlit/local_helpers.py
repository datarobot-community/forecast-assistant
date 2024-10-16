# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from __future__ import annotations
import json
import os
from typing import Any, Dict, Tuple, TYPE_CHECKING

import datarobot as dr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st
from openai import AzureOpenAI
import yaml

if TYPE_CHECKING:
    from kedro.io import DataCatalog


def get_kedro_catalog(kedro_project_root: str) -> DataCatalog:
    """Initialize a kedro data catalog (as a singleton)."""
    try:
        import pathlib
        from kedro.framework.startup import bootstrap_project
        from kedro.framework.session import KedroSession
    except ImportError as e:
        raise ImportError(
            "Please ensure you've installed `kedro` and `kedro_datasets` to run this app locally"
        ) from e

    project_path = pathlib.Path(kedro_project_root).resolve()
    bootstrap_project(project_path)
    session = KedroSession.create(project_path)
    context = session.load_context()
    return context.catalog


def set_session_state(project_root: str):
    try:
        # in production, parameters are available in the working directory
        with open("frontend_config.yaml", "r") as f:
            st.session_state["params"] = yaml.safe_load(f)

        azure_endpoint = os.environ["MLOPS_RUNTIME_PARAM_llm_endpoint"]

        azure_api_key = os.environ["MLOPS_RUNTIME_PARAM_llm_api_key"]
        azure_api_key = json.loads(azure_api_key)["payload"]["apiToken"]
        azure_api_version = os.environ["MLOPS_RUNTIME_PARAM_llm_api_version"]

        st.session_state["azure_client"] = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            api_version=azure_api_version,
        )
        st.session_state["params"]["model_name"] = os.environ[
            "MLOPS_RUNTIME_PARAM_llm_deployment_name"
        ]
        st.session_state["datarobot_api_token"] = os.environ["DATAROBOT_API_TOKEN"]
        st.session_state["datarobot_endpoint"] = os.environ["DATAROBOT_ENDPOINT"]

    except (FileNotFoundError, KeyError):
        # during local dev, parameters can be retrieved from the kedro catalog
        catalog = get_kedro_catalog(project_root)
        params_path = catalog.load("deploy_application.frontend_config")
        with open(params_path, "r") as f:
            st.session_state["params"] = yaml.safe_load(f)
        st.session_state["datarobot_api_token"] = catalog.load(
            "params:credentials.datarobot.api_token"
        )
        st.session_state["datarobot_endpoint"] = catalog.load(
            "params:credentials.datarobot.endpoint"
        )

        azure_credentials = catalog.load(
            "params:credentials.azure_openai_llm_credentials"
        )
        st.session_state["params"]["model_name"] = azure_credentials["deployment_name"]
        st.session_state["azure_client"] = AzureOpenAI(
            azure_endpoint=azure_credentials.get("azure_endpoint"),
            api_key=azure_credentials.get("api_key"),
            api_version=azure_credentials.get("api_version"),
        )


def get_param(parameter: str) -> Any:
    """Get the parameter from the session state"""
    return st.session_state["params"][parameter]


@st.cache_data(show_spinner=False)
def get_scoring_data(endpoint: str, token: str, dataset_id: str) -> pd.DataFrame:
    """Get the scoring data from DataRobot"""
    dr.Client(endpoint=endpoint, token=token)
    return dr.Dataset.get(dataset_id).get_as_dataframe()


@st.cache_data(show_spinner=False)
def make_datarobot_deployment_predictions(
    token: str, data: pd.DataFrame, deployment_id: str
):
    """
    Make predictions on data provided using DataRobot deployment_id provided.
    See docs for details:
         https://docs.datarobot.com/en/docs/api/reference/predapi/dr-predapi.html

    Parameters
    ----------
    data : str
        Feature1,Feature2
        numeric_value,string
    deployment_id : str
        Deployment ID to make predictions with.

    Returns
    -------
    Response schema:
        https://docs.datarobot.com/en/docs/api/reference/predapi/dr-predapi.html#response-schema

    Raises
    ------
    DataRobotPredictionError if there are issues getting predictions from DataRobot
    """
    prediction_server = get_param("prediction_server")

    datarobot_key = prediction_server["datarobot_key"]
    prediction_server_endpoint = prediction_server["url"]

    # Set HTTP headers. The charset should match the contents of the file.
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Authorization": f"Bearer {token}",
        "DataRobot-Key": datarobot_key,
    }
    api_url = os.path.join(
        prediction_server_endpoint,
        "predApi/v1.0/deployments/{deployment_id}/predictions",
    )

    url = api_url.format(deployment_id=deployment_id)

    params = {"maxExplanations": 3}

    # Make API request for predictions
    predictions_response = requests.post(
        url, data=data.to_json(orient="records"), headers=headers, params=params
    )
    # Return a Python dict following the schema in the documentation
    return predictions_response.json()


@st.cache_data(show_spinner=False)
def process_predictions(
    predictions: Dict[str, Any],
) -> pd.DataFrame:
    prediction_interval = str(get_param("prediction_interval"))
    bound_at_zero = get_param("lower_bound_forecast_at_0")

    data = predictions["data"]
    slim_predictions = pd.DataFrame(data)[
        ["seriesId", "timestamp", "prediction", "predictionExplanations"]
    ]
    intervals = pd.DataFrame(
        [i["predictionIntervals"][prediction_interval] for i in data]
    )
    clean_predictions = pd.concat([slim_predictions, intervals], axis=1).drop(
        columns="predictionExplanations"
    )

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


def get_completion(
    client: AzureOpenAI, llm_model_name: str, prompt: str, temperature: float = 0
) -> str:
    """Generate LLM completion"""
    resp = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=llm_model_name,
        temperature=temperature,
    )
    return resp.choices[0].message.content


def get_tldr(
    preds_json: str,
    target: str,
    client: AzureOpenAI,
    llm_model_name: str,
    temperature: float = 0,
) -> Tuple[str, pd.DataFrame]:
    """Get a natural langauge tldr of what the pred expls say about a TS forecast."""
    df = pd.DataFrame(preds_json["data"])

    target_df = pd.DataFrame(
        [
            explanation
            for explanations in df["predictionExplanations"].tolist()
            for explanation in explanations
            if explanation["feature"].startswith(target + " (")
        ]
    )
    target_prompt = get_prompt(target_df, target, ex_target=False)
    target_completion = get_completion(
        client, llm_model_name, target_prompt, temperature=temperature
    )

    ex_target_df = pd.DataFrame(
        [
            explanation
            for explanations in df["predictionExplanations"].tolist()
            for explanation in explanations
            if not explanation["feature"].startswith(target + " (")
        ]
    )
    ex_target_prompt = get_prompt(ex_target_df, target, ex_target=True)
    ex_target_completion = get_completion(
        client, llm_model_name, ex_target_prompt, temperature=temperature
    )
    explain_df = pd.concat((target_df, ex_target_df)).reset_index(drop=True)
    return target_completion + "\n\n\n" + ex_target_completion, explain_df


@st.cache_data(show_spinner=False)
def create_chart(
    history: pd.DataFrame,
    forecast: pd.DataFrame,
    title: str,
):
    datetime_partition_column = get_param("datetime_partition_column")
    target = get_param("target")
    date_format = get_param("date_format")
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

    fig.add_trace(
        go.Scatter(
            x=forecast["timestamp"],
            y=forecast["low"],
            mode="lines",
            name="Low forecast",
            line_shape="spline",
            line=dict(color="#335599", width=0.5, dash="dot"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["timestamp"],
            y=forecast["high"],
            mode="lines",
            name="High forecast",
            line_shape="spline",
            line=dict(color="#335599", width=0.5, dash="dot"),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast["timestamp"],
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
        title_text=get_param("graph_y_axis"),
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
