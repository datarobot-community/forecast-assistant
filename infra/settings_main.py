# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.
import os
from pathlib import Path

import datarobot as dr

from .common.schema import (
    PredictionEnvironmentArgs,
    UseCaseArgs,
)
from .common.stack import get_stack

project_name = get_stack()


try:
    default_prediction_server_id = os.environ["DATAROBOT_PREDICTION_ENVIRONMENT_ID"]
except KeyError as e:
    raise ValueError(
        (
            "Unable to load DataRobot prediction environment id. "
            "Verify you have setup your environment variables as described in README.md."
        )
    ) from e


prediction_environment_args = PredictionEnvironmentArgs(
    resource_name=f"Forecast Assistant Prediction Environment [{project_name}]",
    platform=dr.PredictionEnvironmentPlatform.DATAROBOT_SERVERLESS,  # type: ignore[attr-defined]
)

use_case_args = UseCaseArgs(
    resource_name=f"Forecast Assistant Use Case [{project_name}]",
    description="Use case for Forecast Assistant application",
)

model_training_nb = Path("notebooks/train_model.ipynb")
model_training_output_file = Path(f"frontend/train_model_output.{project_name}.yaml")
scoring_prep_nb = Path("notebooks/prep_scoring_data.ipynb")
scoring_prep_output_file = Path(
    f"notebooks/prep_scoring_data_output.{project_name}.yaml"
)
