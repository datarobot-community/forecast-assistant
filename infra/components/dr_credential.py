# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from typing import List, Optional, Union

import pulumi
import pulumi_datarobot as datarobot

from forecastic.credentials import (
    AzureOpenAICredentials,
    GoogleLLMCredentials,
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
                api_token=credential.api_key,  # type: ignore[union-attr]
                opts=pulumi.ResourceOptions(parent=self),
            )
        elif isinstance(self.credential_raw, GoogleLLMCredentials):
            self.credential = datarobot.GoogleCloudCredential(
                **credential_args.model_dump(),
                # TODO: update & test once declarative api support arrives
                source_file=credential.service_account_key,  # type: ignore[union-attr]
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
                        "AZURE_OPENAI_ENDPOINT",
                        "string",
                        self.credential_raw.azure_endpoint,
                    ),
                    (
                        "AZURE_OPENAI_DEPLOYMENT",
                        "string",
                        self.credential_raw.azure_deployment,
                    ),
                    ("OPENAI_API_VERSION", "string", self.credential_raw.api_version),
                ]
            ]
        elif isinstance(self.credential_raw, GoogleLLMCredentials):
            runtime_parameter_values = [
                datarobot.CustomModelRuntimeParameterValueArgs(
                    key="GOOGLE_SERVICE_ACCOUNT",
                    type="credential",
                    value=self.credential.id,
                ),
            ]
            if self.credential_raw.region is not None:
                runtime_parameter_values.append(
                    datarobot.CustomModelRuntimeParameterValueArgs(
                        key="GOOGLE_REGION",
                        type="string",
                        value=self.credential_raw.region,
                    )
                )
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
                        "AZURE_OPENAI_ENDPOINT",
                        "string",
                        self.credential_raw.azure_endpoint,
                    ),
                    (
                        "AZURE_OPENAI_DEPLOYMENT",
                        "string",
                        self.credential_raw.azure_deployment,
                    ),
                    ("OPENAI_API_VERSION", "string", self.credential_raw.api_version),
                ]
            ]
        elif isinstance(self.credential_raw, GoogleLLMCredentials):
            runtime_parameter_values = [
                datarobot.ApplicationSourceRuntimeParameterValueArgs(
                    key="GOOGLE_SERVICE_ACCOUNT",
                    type="credential",
                    value=self.credential.id,
                ),
            ]
            if self.credential_raw.region is not None:
                runtime_parameter_values.append(
                    datarobot.ApplicationSourceRuntimeParameterValueArgs(
                        key="GOOGLE_REGION",
                        type="string",
                        value=self.credential_raw.region,
                    )
                )
        else:
            raise NotImplementedError("Unsupported credential type")
        return runtime_parameter_values
