# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from enum import Enum

import datarobot as dr
import pulumi
from pydantic import Field
from pydantic_settings import BaseSettings

from .common.schema import (
    PredictionEnvironmentArgs,
    UseCaseArgs,
)

try:
    project_name = pulumi.get_stack()
except KeyError:
    raise ValueError(
        (
            "Unable to retrieve the currently active stack. "
            "Verify you have selected created and selected a stack with `pulumi stack`."
        )
    )


class DatasetType(str, Enum):
    BYO = "byo"
    DEMO = "demo"


default_prediction_server_id = "5f06612df1740600260aca72"


class Settings(BaseSettings):
    dataset_type: DatasetType = Field(default=DatasetType.BYO)


prediction_environment_args = PredictionEnvironmentArgs(
    resource_name="prediction-environment",
    name=f"DocsAssist Prediction Environment [{project_name}]",
    platform=dr.PredictionEnvironmentPlatform.DATAROBOT_SERVERLESS,  # type: ignore[attr-defined]
)

use_case_args = UseCaseArgs(
    resource_name="use-case",
    name=f"Forecastic Use Case [{project_name}]",
    description="Use case for DocsAssist application",
).model_dump(mode="json", exclude_none=True)
