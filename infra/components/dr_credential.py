# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

import json
from typing import List, Optional, Union

import pulumi
import pulumi_datarobot as datarobot

from forecastic.credentials import (
    AzureOpenAICredentials,
    LLMCredentials,
)

from ..common.schema import (
    CredentialArgs,
)


class DRCredential(pulumi.ComponentResource):
    """DR Credential for use with a custom deployment or app.

    Abstracts creation of the appropriate credential type, structuring runtime parameters.
    """

    def __init__(
        self,
        resource_name: str,
        credential: LLMCredentials,
        credential_args: CredentialArgs,
        opts: Optional[pulumi.ResourceOptions] = None,
    ):
        super().__init__("custom:datarobot:DRCredential", resource_name, None, opts)

        self.credential_raw = credential
        self.credential: Union[
            datarobot.ApiTokenCredential, datarobot.GoogleCloudCredential
        ]
        if isinstance(self.credential_raw, AzureOpenAICredentials):
            self.credential = datarobot.ApiTokenCredential(
                **credential_args.model_dump(),
                api_token=credential.api_key,
                opts=pulumi.ResourceOptions(parent=self),
            )
        else:
            raise ValueError("Unsupported credential type")

        self.register_outputs(
            {
                "id": self.credential.id,
            }
        )

    @property
    def runtime_parameter_values(
        self,
    ) -> List[datarobot.CustomModelRuntimeParameterValueArgs]:
        if isinstance(self.credential_raw, AzureOpenAICredentials):
            runtime_parameter_values = [
                datarobot.CustomModelRuntimeParameterValueArgs(
                    key=key,
                    type=type_,
                    value=value,  # type: ignore[arg-type]
                )
                for key, type_, value in [
                    ("OPENAI_API_KEY", "credential", self.credential.id),
                    (
                        "OPENAI_API_BASE",
                        "string",
                        self.credential_raw.azure_endpoint,
                    ),
                    (
                        "OPENAI_API_DEPLOYMENT_ID",
                        "string",
                        self.credential_raw.azure_deployment,
                    ),
                    ("OPENAI_API_VERSION", "string", self.credential_raw.api_version),
                ]
            ]
        else:
            raise NotImplementedError("Unsupported credential type")
        return runtime_parameter_values

    @property
    def app_runtime_parameter_values(
        self,
    ) -> List[datarobot.ApplicationSourceRuntimeParameterValueArgs]:
        if isinstance(self.credential_raw, AzureOpenAICredentials):
            runtime_parameter_values = [
                datarobot.ApplicationSourceRuntimeParameterValueArgs(
                    key=key,
                    type=type_,
                    value=value,  # type: ignore[arg-type]
                )
                for key, type_, value in [
                    ("OPENAI_API_KEY", "credential", self.credential.id),
                    (
                        "OPENAI_API_BASE",
                        "string",
                        json.dumps({"payload": self.credential_raw.azure_endpoint}),
                    ),
                    (
                        "OPENAI_API_DEPLOYMENT_ID",
                        "string",
                        json.dumps({"payload": self.credential_raw.azure_deployment}),
                    ),
                    (
                        "OPENAI_API_VERSION",
                        "string",
                        json.dumps({"payload": self.credential_raw.api_version}),
                    ),
                ]
            ]
        else:
            raise NotImplementedError("Unsupported credential type")
        return runtime_parameter_values
