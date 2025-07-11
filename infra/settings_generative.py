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
from __future__ import annotations

import datarobot as dr
import pulumi_datarobot as datarobot
from datarobot_pulumi_utils.schema.custom_models import (
    CustomModelArgs,
    DeploymentArgs,
    RegisteredModelArgs,
)
from datarobot_pulumi_utils.schema.exec_envs import (
    RuntimeEnvironments,
)
from datarobot_pulumi_utils.schema.llms import LLMBlueprintArgs, LLMs, PlaygroundArgs

from forecastic.schema import GenerativeDeploymentSettings, association_id

from .settings_main import (
    default_prediction_server_id,
    project_name,
)

LLM = LLMs.AZURE_OPENAI_GPT_4_O_MINI

if LLM is not None:
    playground_args = PlaygroundArgs(
        resource_name=f"Forecasting Assistant Playground [{project_name}]",
    )

    llm_blueprint_args = LLMBlueprintArgs(
        resource_name=f"Forecasting Assistant LLM Blueprint [{project_name}]",
        llm_id=LLM.name,
        llm_settings=datarobot.LlmBlueprintLlmSettingsArgs(
            max_completion_length=512,
            temperature=0.5,
        ),
    )

    custom_model_args = CustomModelArgs(
        resource_name=f"Forecasting Assistant Generative Custom Model [{project_name}]",
        name=f"Forecasting Assistant Generative Custom Model [{project_name}]",
        base_environment_id=RuntimeEnvironments.PYTHON_312_MODERATIONS.value.id,
        target_name=GenerativeDeploymentSettings().target_feature_name,
        target_type=dr.enums.TARGET_TYPE.TEXT_GENERATION,
    )

    registered_model_args = RegisteredModelArgs(
        resource_name=f"Forecasting Assistant Generative Registered Model [{project_name}]",
    )

    deployment_args = DeploymentArgs(
        resource_name=f"Forecasting Assistant Generative Deployment [{project_name}]",
        label=f"Forecasting Assistant Generative Deployment [{project_name}]",
        association_id_settings=datarobot.DeploymentAssociationIdSettingsArgs(
            column_names=[association_id],
            auto_generate_id=False,
            required_in_prediction_requests=True,
        ),
        predictions_settings=(
            None
            if default_prediction_server_id
            else datarobot.DeploymentPredictionsSettingsArgs(
                min_computes=0, max_computes=1
            )
        ),
        predictions_data_collection_settings=datarobot.DeploymentPredictionsDataCollectionSettingsArgs(
            enabled=True,
        ),
    )
