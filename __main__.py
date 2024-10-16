# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

import time

import datarobot as dr
import pulumi
import pulumi_datarobot as datarobot
from datarobotx.idp.registered_model_versions import (
    get_or_create_registered_leaderboard_model_version,
)
from datarobotx.idp.use_cases import get_or_create_use_case

from infra import (
    prepare_app,
    settings_app_infra,
    settings_deploy_forecasts,
    settings_load_dataset,
    settings_main,
)
from infra.components.dr_credential import DRCredential
from infra.deploy_forecasts import run_ts_autopilot
from infra.load_datasets import load_datasets
from infra.settings_llm_credential import credential, credential_args
from infra.settings_production import (
    auto_stopping_app,
    update_batch_prediction_job,
    update_retraining_policy,
)

client = dr.client.get_client()

DATAROBOT_API_TOKEN = client.token
DATAROBOT_ENDPOINT = client.endpoint

start_time = time.time()

pulumi.log.info("Creating use case")
use_case_id = get_or_create_use_case(
    token=DATAROBOT_API_TOKEN,
    endpoint=DATAROBOT_ENDPOINT,
    name=settings_main.use_case_args["name"],
    description=settings_main.use_case_args["description"],
)

# use_case = datarobot.UseCase(
#     **settings_main.use_case_args, opts=pulumi.ResourceOptions(import_=use_case_id)
# )
pulumi.log.info("Creating Datasets")
dataset_train_id, dataset_scoring_id = load_datasets(
    use_case_id,
    training_dataset_args=settings_load_dataset.training_dataset,
    scoring_dataset_args=settings_load_dataset.scoring_dataset,
)
pulumi.log.info("Running Autopilot")
project_id, recommended_model_id, calendar_id = run_ts_autopilot(
    create_calendar_args=settings_deploy_forecasts.calendar_args,
    autopilotrun_args=settings_deploy_forecasts.autopilotrun_args,
    training_dataset_id=dataset_train_id,
    use_case_id=use_case_id,
)

pulumi.log.info("Creating Registered Model")
registered_model_version_id = get_or_create_registered_leaderboard_model_version(
    token=DATAROBOT_API_TOKEN,
    endpoint=DATAROBOT_ENDPOINT,
    model_id=recommended_model_id,
    registered_model_name=settings_deploy_forecasts.registered_model_args.name,
)

pulumi.log.info("Preparing App assets")
app_files = prepare_app.gather_assets(
    project_id=project_id,
    recommended_model_id=recommended_model_id,
    scoring_dataset_id=dataset_scoring_id,
)

# =============================== drx-idp Land ↑ ================================================ #
#                                                                                                 #
#                                                                                                 #
# =============================== Pulumi Land ↓ ================================================= #

if settings_main.default_prediction_server_id is None:
    prediction_environment = datarobot.PredictionEnvironment(
        **settings_main.prediction_environment_args.model_dump(exclude_none=True),
    )
else:
    prediction_environment = dr.PredictionEnvironment.get(  # type: ignore[attr-defined]
        settings_main.default_prediction_server_id
    )


deployment = datarobot.Deployment(
    prediction_environment_id=prediction_environment.id,
    registered_model_version_id=registered_model_version_id,
    **settings_deploy_forecasts.get_deployment_args(project_id=project_id).model_dump(),
)


llm_credential = DRCredential(
    resource_name="llm-credential",
    credential=credential,
    credential_args=credential_args,
)


app_runtime_parameters = [
    datarobot.ApplicationSourceRuntimeParameterValueArgs(
        key="deployment_id",
        type="deployment",
        value=deployment.id,
    )
] + llm_credential.app_runtime_parameter_values


application_source = datarobot.ApplicationSource(
    files=app_files,
    runtime_parameter_values=app_runtime_parameters,
    **settings_app_infra.app_source_args,
)

app = datarobot.CustomApplication(
    resource_name=settings_app_infra.app_resource_name,
    name=settings_app_infra.app_name,
    source_version_id=application_source.version_id,
)

deployment.id.apply(
    func=lambda deployment_id: update_batch_prediction_job(
        deployment_id=deployment_id, dataset_scoring_id=dataset_scoring_id
    )
)

deployment.id.apply(
    func=lambda deployment_id: update_retraining_policy(
        deployment_id=deployment_id,
        calendar_id=calendar_id,
        training_dataset_id=dataset_train_id,
    )
)

app.id.apply(auto_stopping_app)


pulumi.export("deployment_id", deployment.id)
pulumi.export("app_url", app.application_url)
