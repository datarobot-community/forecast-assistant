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

import os
from pathlib import Path

from infra.common.globals import GlobalPredictionEnvironmentPlatforms

from .common.schema import (
    PredictionEnvironmentArgs,
    UseCaseArgs,
)
from .common.stack import get_stack

project_name = get_stack()


default_prediction_server_id = os.getenv("DATAROBOT_PREDICTION_ENVIRONMENT_ID", None)

prediction_environment_args = PredictionEnvironmentArgs(
    resource_name=f"Forecast Assistant Prediction Environment [{project_name}]",
    platform=GlobalPredictionEnvironmentPlatforms.DATAROBOT_SERVERLESS,
).model_dump(mode="json", exclude_none=True)


use_case_args = UseCaseArgs(
    resource_name=f"Forecast Assistant Use Case [{project_name}]",
    description="Use case for Forecast Assistant application",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.absolute()

model_training_nb = PROJECT_ROOT / "notebooks" / "train_model.ipynb"
model_training_output_name = f"train_model_output.{project_name}.yaml"
model_training_output_file = PROJECT_ROOT / "forecastic" / model_training_output_name
scoring_prep_nb = PROJECT_ROOT / "notebooks" / "prep_scoring_data.ipynb"
scoring_prep_output_file = (
    PROJECT_ROOT / "notebooks" / f"prep_scoring_data_output.{project_name}.yaml"
)
