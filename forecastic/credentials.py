# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.
from __future__ import annotations

from typing import Optional, Union

from pydantic import AliasChoices, AliasPath, Field
from pydantic_settings import (
    BaseSettings,
)


class AzureOpenAICredentials(BaseSettings):
    """LLM credentials auto-constructed using environment variables."""

    api_version: str = Field(
        validation_alias=AliasChoices(
            "MLOPS_RUNTIME_PARAM_OPENAI_API_VERSION",
            "OPENAI_API_VERSION",
        )
    )
    azure_endpoint: str = Field(
        validation_alias=AliasChoices(
            "MLOPS_RUNTIME_PARAM_AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_ENDPOINT",
        )
    )
    api_key: str = Field(
        validation_alias=AliasChoices(
            AliasPath("MLOPS_RUNTIME_PARAM_OPENAI_API_KEY", "payload", "apiToken"),
            "OPENAI_API_KEY",
        )
    )
    azure_deployment: str = Field(
        validation_alias=AliasChoices(
            "MLOPS_RUNTIME_PARAM_AZURE_OPENAI_DEPLOYMENT",
            "AZURE_OPENAI_DEPLOYMENT",
        )
    )


class GoogleLLMCredentials(BaseSettings):
    service_account_key: str = Field(
        validation_alias=AliasChoices(
            AliasPath(
                "MLOPS_RUNTIME_PARAM_GOOGLE_SERVICE_ACCOUNT", "payload", "gcpKey"
            ),
            "GOOGLE_SERVICE_ACCOUNT",
        )
    )
    region: Optional[str] = Field(
        validation_alias=AliasChoices(
            "MLOPS_RUNTIME_PARAM_GOOGLE_REGION",
            "GOOGLE_REGION",
        ),
        default=None,
    )


LLMCredentials = Union[AzureOpenAICredentials, GoogleLLMCredentials]
