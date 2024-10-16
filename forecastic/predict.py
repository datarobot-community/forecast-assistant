# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import datarobot as dr
import pandas as pd
from datarobot.models.deployment.deployment import Deployment
from datarobot_predict.deployment import predict
from openai import AzureOpenAI
from pydantic import ValidationError

from forecastic.credentials import AzureOpenAICredentials

from .deployments import TimeSeriesDeployment

try:
    time_series_deployment_id = TimeSeriesDeployment().id
    credentials = AzureOpenAICredentials()
    azure_client = AzureOpenAI(
        azure_endpoint=credentials.azure_endpoint,
        api_key=credentials.api_key,
        api_version=credentials.api_version,
    )
except ValidationError as e:
    raise ValueError(
        (
            "Unable to load DataRobot deployment ids. If running locally, verify you have selected "
            "the correct stack and that it is active using `pulumi stack output`. "
            "If running in DataRobot, verify your runtime parameters have been set correctly."
        )
    ) from e


@dataclass
class DeploymentInfo:
    deployment: Deployment
    target_name: str


def _get_deployment_info(deployment_id: str) -> DeploymentInfo:
    deployment = dr.Deployment.get(deployment_id)  # type: ignore[attr-defined]
    target_name = deployment.model["target_name"]  # type: ignore[index]
    return DeploymentInfo(deployment, str(target_name))


def make_datarobot_predictions(data: pd.DataFrame) -> pd.DataFrame:
    deployment_info = _get_deployment_info(time_series_deployment_id)
    prediction = predict(
        deployment=deployment_info.deployment,
        data_frame=data,
        max_explanations=3,
    ).dataframe
    return prediction


def get_completion(
    prompt: str,
    temperature: float = 0,
    system_prompt: Optional[str] = None,
    llm_model_name: Optional[str] = None,
) -> str:
    """Generate LLM completion"""
    if system_prompt:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
    else:
        messages = [{"role": "user", "content": prompt}]
    resp = azure_client.chat.completions.create(
        messages=messages,  # type: ignore[arg-type]
        model=llm_model_name
        if llm_model_name is not None
        else credentials.azure_deployment,
        temperature=temperature,
    )
    return str(resp.choices[0].message.content)
