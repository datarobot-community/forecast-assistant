# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.
from __future__ import annotations

from typing import Union

from pydantic import AliasChoices, AliasPath, Field
from pydantic_settings import (
    BaseSettings,
)


class AzureOpenAICredentials(BaseSettings):
    """LLM credentials auto-constructed using environment variables."""

    api_version: str = Field(
        validation_alias=AliasChoices(
            AliasPath("MLOPS_RUNTIME_PARAM_OPENAI_API_VERSION", "payload"),
            "OPENAI_API_VERSION",
        ),
    )
    azure_endpoint: str = Field(
        validation_alias=AliasChoices(
            AliasPath("MLOPS_RUNTIME_PARAM_OPENAI_API_BASE", "payload"),
            "OPENAI_API_BASE",
        )
    )
    api_key: str = Field(
        validation_alias=AliasChoices(
            AliasPath("MLOPS_RUNTIME_PARAM_OPENAI_API_KEY", "payload", "apiToken"),
            "OPENAI_API_KEY",
        ),
    )
    azure_deployment: str = Field(
        validation_alias=AliasChoices(
            AliasPath("MLOPS_RUNTIME_PARAM_OPENAI_API_DEPLOYMENT_ID", "payload"),
            "OPENAI_API_DEPLOYMENT_ID",
        )
    )

    def test(self) -> None:
        import openai

        try:
            client = openai.AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.azure_endpoint,
                api_version=self.api_version,
            )
            client.chat.completions.create(
                messages=[{"role": "user", "content": "hello"}],
                model=self.azure_deployment,
            )
        except Exception as e:
            raise ValueError(
                f"Unable to run a successful test completion against model '{self.azure_deployment}' "
                "with provided Azure OpenAI credentials. Please validate your credentials."
            ) from e


LLMCredentials = Union[AzureOpenAICredentials]
