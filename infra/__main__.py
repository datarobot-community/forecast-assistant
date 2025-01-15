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

import pathlib
import sys

import pulumi
import pulumi_datarobot as datarobot
import yaml

sys.path.append("..")

from forecastic.i18n import LocaleSettings
from forecastic.resources import (
    ScoringDataset,
    app_env_name,
    scoring_dataset_env_name,
    time_series_deployment_env_name,
)
from forecastic.schema import AppSettings
from infra import (
    settings_app_infra,
    settings_forecast_deployment,
    settings_main,
)
from infra.common.feature_flags import check_feature_flags
from infra.common.papermill import run_notebook
from infra.common.urls import get_deployment_url
from infra.components.dr_credential import DRCredential
from infra.settings_forecast_deployment import (
    ensure_batch_prediction_job,
    ensure_retraining_policy,
    update_dynamic_deployment_settings,
)
from infra.settings_llm_credential import credential, credential_args
from infra.settings_main import (
    model_training_nb,
    model_training_output_file,
    scoring_prep_nb,
    scoring_prep_output_file,
)

LocaleSettings().setup_locale()

check_feature_flags(pathlib.Path("feature_flag_requirements.yaml"))

if not model_training_output_file.exists():
    pulumi.info("Executing model training notebook...")
    run_notebook(model_training_nb)
else:
    pulumi.info(
        f"Using existing model training outputs in '{model_training_output_file}'"
    )
with open(model_training_output_file) as f:
    model_training_output = AppSettings(**yaml.safe_load(f))


if not scoring_prep_output_file.exists():
    pulumi.info("Executing scoring data prep notebook...")
    run_notebook(scoring_prep_nb)
else:
    pulumi.info(
        f"Using existing scoring data prep outputs in '{scoring_prep_output_file}'"
    )
with open(scoring_prep_output_file) as f:
    scoring_prep_output = ScoringDataset(**yaml.safe_load(f))


if settings_main.default_prediction_server_id is None:
    prediction_environment = datarobot.PredictionEnvironment(
        **settings_main.prediction_environment_args,
    )
else:
    prediction_environment = datarobot.PredictionEnvironment.get(
        "Forecast Assistant Prediction Environment [PRE-EXISTING]",
        settings_main.default_prediction_server_id,
    )

update_dynamic_deployment_settings(
    settings_forecast_deployment.deployment_args,
    datetime_partition_column=model_training_output.datetime_partition_column_transformed,
    date_format=model_training_output.date_format,
    prediction_interval=model_training_output.prediction_interval,
)
forecast_deployment = datarobot.Deployment(
    prediction_environment_id=prediction_environment.id,
    registered_model_version_id=model_training_output.registered_model_version_id,
    **settings_forecast_deployment.deployment_args.model_dump(),
    use_case_ids=[model_training_output.use_case_id],
)

forecast_deployment.id.apply(
    func=lambda deployment_id: ensure_batch_prediction_job(
        deployment_id=deployment_id, dataset_scoring_id=scoring_prep_output.id
    )
)


pulumi.Output.all(
    deployment_id=forecast_deployment.id,
    prediction_environment_id=prediction_environment.id,
).apply(
    lambda kwargs: ensure_retraining_policy(
        calendar_id=model_training_output.calendar_id,
        training_dataset_id=scoring_prep_output.id,
        **kwargs,
    )
)

llm_credential = DRCredential(
    resource_name=f"Generic LLM Credential [{settings_main.project_name}]",
    credential=credential,
    credential_args=credential_args,
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
] + llm_credential.app_runtime_parameter_values

application_source = datarobot.ApplicationSource(
    files=settings_app_infra.get_app_files(app_runtime_parameters),
    runtime_parameter_values=app_runtime_parameters,
    **settings_app_infra.app_source_args,
)

app = datarobot.CustomApplication(
    resource_name=settings_app_infra.app_resource_name,
    source_version_id=application_source.version_id,
    use_case_ids=[model_training_output.use_case_id],
)

app.id.apply(settings_app_infra.ensure_app_settings)


pulumi.export(time_series_deployment_env_name, forecast_deployment.id)
pulumi.export(scoring_dataset_env_name, scoring_prep_output.id)
pulumi.export(
    settings_forecast_deployment.deployment_args.resource_name,
    forecast_deployment.id.apply(get_deployment_url),
)
pulumi.export(app_env_name, app.id)
pulumi.export(settings_app_infra.app_resource_name, app.application_url)
