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

import os
import sys
import textwrap
from pathlib import Path

import pulumi
import pulumi_datarobot as datarobot
import yaml
from datarobot_pulumi_utils.common import check_feature_flags
from datarobot_pulumi_utils.common.urls import get_deployment_url
from datarobot_pulumi_utils.pulumi.custom_model_deployment import CustomModelDeployment
from datarobot_pulumi_utils.pulumi.proxy_llm_blueprint import ProxyLLMBlueprint
from datarobot_pulumi_utils.schema.llms import LLMs

sys.path.append("..")

from forecastic.credentials import DRCredentials
from forecastic.i18n import LocaleSettings
from forecastic.resources import (
    ScoringDataset,
    app_env_name,
    generative_deployment_env_name,
    scoring_dataset_env_name,
    time_series_deployment_env_name,
)
from forecastic.schema import AppSettings
from infra import (
    settings_app_infra,
    settings_forecast_deployment,
    settings_generative,
    settings_main,
)
from infra.settings_forecast_deployment import (
    get_deployment_args,
)
from infra.settings_main import (
    model_training_nb,
    model_training_output_file,
    scoring_prep_nb,
    scoring_prep_output_file,
)
from infra.settings_proxy_llm import CHAT_MODEL_NAME
from utils.credentials import (
    get_credential_runtime_parameter_values,
    get_credentials,
)
from utils.papermill import run_notebook

TEXTGEN_DEPLOYMENT_ID = os.environ.get("TEXTGEN_DEPLOYMENT_ID")
TEXTGEN_REGISTERED_MODEL_ID = os.environ.get("TEXTGEN_REGISTERED_MODEL_ID")
# Set FORECAST_DEPLOYMENT_ID to use an existing forecast deployment instead of creating a new one
FORECAST_DEPLOYMENT_ID = os.environ.get("FORECAST_DEPLOYMENT_ID")

if settings_generative.LLM == LLMs.DEPLOYED_LLM:
    pulumi.info(f"{TEXTGEN_DEPLOYMENT_ID=}")
    pulumi.info(f"{TEXTGEN_REGISTERED_MODEL_ID=}")
    if (TEXTGEN_DEPLOYMENT_ID is None) == (TEXTGEN_REGISTERED_MODEL_ID is None):  # XOR
        raise ValueError(
            "Either TEXTGEN_DEPLOYMENT_ID or TEXTGEN_REGISTERED_MODEL_ID must be set when using a deployed LLM. Please check your .env file"
        )

LocaleSettings().setup_locale()

check_feature_flags(Path("feature_flag_requirements.yaml"))

if not model_training_output_file.exists():
    pulumi.info("Executing model training notebook...")
    run_notebook(model_training_nb)
else:
    pulumi.info(
        f"Using existing model training outputs in '{model_training_output_file}'"
    )

with open(model_training_output_file) as f:
    model_training_output = AppSettings(**yaml.safe_load(f))

use_case = datarobot.UseCase.get(
    id=model_training_output.use_case_id,
    resource_name="Forecasting Assistant Use Case",
)

if not scoring_prep_output_file.exists():
    pulumi.info("Executing scoring data prep notebook...")
    run_notebook(scoring_prep_nb)
else:
    pulumi.info(
        f"Using existing scoring data prep outputs in '{scoring_prep_output_file}'"
    )
with open(scoring_prep_output_file) as f:
    scoring_dataset_id = yaml.safe_load(f)["id"]
    scoring_prep_output = ScoringDataset.model_construct(id=scoring_dataset_id)


if settings_main.default_prediction_server_id is None:
    prediction_environment = datarobot.PredictionEnvironment(
        **settings_main.prediction_environment_args,
    )
else:
    prediction_environment = datarobot.PredictionEnvironment.get(
        "Forecast Assistant Prediction Environment [PRE-EXISTING]",
        settings_main.default_prediction_server_id,
    )

deployment_args = get_deployment_args(
    datetime_partition_column=model_training_output.datetime_partition_column_transformed,
    date_format=model_training_output.date_format,
    prediction_interval=model_training_output.prediction_interval,
)

# Check if using an existing forecast deployment or creating a new one
if FORECAST_DEPLOYMENT_ID is not None:
    pulumi.info(f"Using existing forecast deployment: {FORECAST_DEPLOYMENT_ID}")
    forecast_deployment = datarobot.Deployment.get(
        resource_name="Existing Forecast Deployment",
        id=FORECAST_DEPLOYMENT_ID,
    )
else:
    pulumi.info("Creating new forecast deployment...")
    forecast_deployment = datarobot.Deployment(
        prediction_environment_id=prediction_environment.id,
        registered_model_version_id=model_training_output.registered_model_version_id,
        **deployment_args.model_dump(),
        use_case_ids=[model_training_output.use_case_id],
    )

# Only create batch prediction job and retraining policy for new deployments
if FORECAST_DEPLOYMENT_ID is None:
    batch_prediction_job = datarobot.BatchPredictionJobDefinition(
        resource_name=settings_forecast_deployment.batch_prediction_job_name,
        enabled=True,
        deployment_id=forecast_deployment.id,
        intake_settings=datarobot.BatchPredictionJobDefinitionIntakeSettingsArgs(
            type="dataset", dataset_id=scoring_dataset_id
        ),
        output_settings=datarobot.BatchPredictionJobDefinitionOutputSettingsArgs(
            type="localFile"
        ),
        schedule=settings_forecast_deployment.batch_prediction_job_schedule,
    )

    retraining_policy = datarobot.DeploymentRetrainingPolicy(
        deployment_id=forecast_deployment.id,
        **settings_forecast_deployment.retraining_policy_settings.model_dump(),
    )
else:
    pulumi.info(
        "Skipping batch prediction job and retraining policy creation for existing deployment"
    )

app_runtime_parameters = [
    datarobot.ApplicationSourceRuntimeParameterValueArgs(
        key=time_series_deployment_env_name,
        type="deployment",
        value=forecast_deployment.id,
    ),
    datarobot.ApplicationSourceRuntimeParameterValueArgs(
        key=scoring_dataset_env_name,
        type="string",
        value=scoring_prep_output.id,
    ),
    datarobot.ApplicationSourceRuntimeParameterValueArgs(
        key="APP_LOCALE", type="string", value=LocaleSettings().app_locale
    ),
]

credentials: DRCredentials | None

try:
    credentials = get_credentials(settings_generative.LLM)
except ValueError:
    raise
except TypeError:
    pulumi.warn(
        textwrap.dedent("""\
        Failed to find credentials for LLM. Continuing deployment without LLM support.

        If you intended to provide credentials, please consult the Readme and follow the instructions.
        """)
    )
    credentials = None

credentials_runtime_parameters_values = get_credential_runtime_parameter_values(
    credentials
)

if credentials is not None or (
    settings_generative.LLM == LLMs.DEPLOYED_LLM
    and (TEXTGEN_REGISTERED_MODEL_ID is not None or TEXTGEN_DEPLOYMENT_ID is not None)
):
    playground = datarobot.Playground(
        use_case_id=use_case.id,
        **settings_generative.playground_args.model_dump(),
    )

    if settings_generative.LLM == LLMs.DEPLOYED_LLM:
        if TEXTGEN_REGISTERED_MODEL_ID is not None:
            proxy_llm_registered_model = datarobot.RegisteredModel.get(
                resource_name="Existing TextGen Registered Model",
                id=TEXTGEN_REGISTERED_MODEL_ID,
            )

            proxy_llm_deployment = datarobot.Deployment(
                resource_name=f"Forecasting Assistant LLM Deployment [{settings_main.project_name}]",
                registered_model_version_id=proxy_llm_registered_model.version_id,
                prediction_environment_id=prediction_environment.id,
                label=f"Forecasting Assistant LLM Deployment [{settings_main.project_name}]",
                use_case_ids=[use_case.id],
                opts=pulumi.ResourceOptions(
                    replace_on_changes=["registered_model_version_id"]
                ),
            )
        elif TEXTGEN_DEPLOYMENT_ID is not None:
            proxy_llm_deployment = datarobot.Deployment.get(
                resource_name="Existing LLM Deployment", id=TEXTGEN_DEPLOYMENT_ID
            )
        else:
            raise ValueError(
                "Either TEXTGEN_REGISTERED_MODEL_ID or TEXTGEN_DEPLOYMENT_ID have to be set in `.env`"
            )

        llm_blueprint = ProxyLLMBlueprint(
            use_case_id=use_case.id,
            playground_id=playground.id,
            proxy_llm_deployment_id=proxy_llm_deployment.id,
            chat_model_name=CHAT_MODEL_NAME,
            **settings_generative.llm_blueprint_args.model_dump(mode="python"),
        )

    elif settings_generative.LLM != LLMs.DEPLOYED_LLM:
        llm_blueprint = datarobot.LlmBlueprint(  # type: ignore[assignment]
            playground_id=playground.id,
            **settings_generative.llm_blueprint_args.model_dump(),
        )

    generative_custom_model = datarobot.CustomModel(
        **settings_generative.custom_model_args.model_dump(exclude_none=True),
        use_case_ids=[use_case.id],
        source_llm_blueprint_id=llm_blueprint.id,
        runtime_parameter_values=[]
        if settings_generative.LLM.name == LLMs.DEPLOYED_LLM.name
        else credentials_runtime_parameters_values,
    )

    generative_deployment = CustomModelDeployment(
        resource_name=f"Forecasting Assistant LLM Deployment [{settings_main.project_name}]",
        custom_model_version_id=generative_custom_model.version_id,
        registered_model_args=settings_generative.registered_model_args,
        prediction_environment=prediction_environment,
        deployment_args=settings_generative.deployment_args,
        use_case_ids=[use_case.id],
    )

    app_runtime_parameters.append(
        datarobot.ApplicationSourceRuntimeParameterValueArgs(
            key=generative_deployment_env_name,
            type="deployment",
            value=generative_deployment.id,
        ),
    )

    pulumi.export(generative_deployment_env_name, generative_deployment.id)


application_source = datarobot.ApplicationSource(
    files=settings_app_infra.get_app_files(app_runtime_parameters),
    runtime_parameter_values=app_runtime_parameters,
    **settings_app_infra.app_source_args,
)

app = datarobot.CustomApplication(
    resource_name=settings_app_infra.app_resource_name,
    source_version_id=application_source.version_id,
    use_case_ids=[model_training_output.use_case_id],
    allow_auto_stopping=True,
)


pulumi.export(time_series_deployment_env_name, forecast_deployment.id)
pulumi.export(scoring_dataset_env_name, scoring_prep_output.id)
pulumi.export(
    deployment_args.resource_name,
    forecast_deployment.id.apply(get_deployment_url),
)
pulumi.export(app_env_name, app.id)
pulumi.export(settings_app_infra.app_resource_name, app.application_url)
