# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from typing import Optional

import pulumi
import pulumi_datarobot as datarobot

from ..common.schema import CustomModelArgs, DeploymentArgs, RegisteredModelArgs


class CustomModelDeployment(pulumi.ComponentResource):
    def __init__(
        self,
        resource_name: str,
        registered_model_args: RegisteredModelArgs,
        prediction_environment: datarobot.PredictionEnvironment,
        deployment_args: DeploymentArgs,
        custom_model_version_id: Optional[pulumi.Input[str]] = None,
        custom_model_args: Optional[CustomModelArgs] = None,
        opts: Optional[pulumi.ResourceOptions] = None,
    ):
        """
        Deploy a custom model in DataRobot.

        This class performs the following steps:
        1. Registers the custom model.
        2. Deploys the registered model to the specified prediction environment.

        Parameters:
        -----------
        name : str
            The name of this Pulumi resource.
        custom_model : datarobot.CustomModel
            The custom model to be deployed.
        prediction_environment : datarobot.PredictionEnvironment
            The DataRobot PredictionEnvironment object where the model will be deployed.
        registered_model_args : RegisteredModelArgs
            Arguments for registering the model.
        deployment_args : DeploymentArgs
            Arguments for creating the Deployment.
        opts : Optional[pulumi.ResourceOptions]
            Optional Pulumi resource options.
        """
        super().__init__(
            "custom:datarobot:CustomModelDeployment", resource_name, None, opts
        )
        if (custom_model_version_id and custom_model_args) or (
            not custom_model_version_id and not custom_model_args
        ):
            raise ValueError(
                "Exactly one of custom_model_version_id and custom_model_args must be specified"
            )

        if custom_model_args:
            custom_model_version_id = datarobot.CustomModel(
                **custom_model_args.model_dump(exclude_none=True),
                opts=pulumi.ResourceOptions(parent=self),
            ).version_id
        self.registered_model = datarobot.RegisteredModel(
            custom_model_version_id=custom_model_version_id,
            **registered_model_args.model_dump(mode="json"),
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.deployment = datarobot.Deployment(
            prediction_environment_id=prediction_environment.id,
            registered_model_version_id=self.registered_model.version_id,
            **deployment_args.model_dump(),
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs(
            {
                "custom_model_version_id": custom_model_version_id,
                "registered_model_id": self.registered_model.id,
                "registered_model_version_id": self.registered_model.version_id,
                "deployment_id": self.deployment.id,
            }
        )

    @property
    def id(self) -> pulumi.Output[str]:
        return self.deployment.id

    @property
    def deployment_id(self) -> pulumi.Output[str]:
        return self.deployment.id

    @property
    def registered_model_id(self) -> pulumi.Output[str]:
        return self.registered_model.id

    @property
    def registered_model_version_id(self) -> pulumi.Output[str]:
        return self.registered_model.version_id
