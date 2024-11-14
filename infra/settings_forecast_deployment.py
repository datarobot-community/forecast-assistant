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

from typing import cast

import datarobot as dr
import pulumi_datarobot as datarobot
from datarobot.models.batch_job import Schedule as DatarobotSchedule
from datarobotx.idp.batch_predictions import get_update_or_create_batch_prediction_job
from datarobotx.idp.retraining_policies import get_update_or_create_retraining_policy

from .common.schema import (
    DeploymentArgs,
)
from .common.schema_batch_predictions import (
    BatchPredictionJobDefinitionsCreate,
    Catalog,
    LocalFileOutput,
)
from .common.schema_retraining import (
    Action,
    AutopilotOptions,
    CVMethod,
    FeatureListStrategy,
    ModelSelectionStrategy,
    ProjectOptions,
    ProjectOptionsStrategy,
    RetrainingPolicyCreate,
    Schedule,
    TimeSeriesOptions,
    Trigger,
    TriggerType,
)
from .settings_main import default_prediction_server_id, project_name

deployment_args = DeploymentArgs(
    resource_name=f"Forecast Assistant Deployment [{project_name}]",
    label=f"Forecast Assistant Deployment [{project_name}]",
    association_id_settings=datarobot.DeploymentAssociationIdSettingsArgs(
        column_names=["association_id"],
        auto_generate_id=False,
        required_in_prediction_requests=False,
    ),
    predictions_settings=(
        None
        if default_prediction_server_id is not None
        else datarobot.DeploymentPredictionsSettingsArgs(
            min_computes=0, max_computes=1, real_time=True
        )
    ),
    predictions_data_collection_settings=datarobot.DeploymentPredictionsDataCollectionSettingsArgs(
        enabled=True
    ),
    drift_tracking_settings=datarobot.DeploymentDriftTrackingSettingsArgs(
        feature_drift_enabled=True, target_drift_enabled=True
    ),
)


retraining_policy_settings = RetrainingPolicyCreate(
    name="Retrain on Accuracy Decline",
    description="",
    action=Action.ModelReplacement,
    autopilotOptions=AutopilotOptions(
        mode=dr.enums.AUTOPILOT_MODE.QUICK,
        blendBestModels=False,
        shapOnlyMode=False,
        runLeakageRemovedFeatureList=True,
    ),
    trigger=Trigger(
        type=TriggerType.accuracy_decline,
        schedule=Schedule(
            minute=[0],
            hour=[0],
            dayOfMonth=["*"],
            month=["*"],
            dayOfWeek=["*"],
        ),
        statusDeclinesToWarning=True,
        statusDeclinesToFailing=False,
        statusStillInDecline=False,
    ),
    projectOptionsStrategy=ProjectOptionsStrategy.SameAsChampion,
    featureListStrategy=FeatureListStrategy.InformativeFeatures,
    modelSelectionStrategy=ModelSelectionStrategy.AutopilotRecommended,
    projectOptions=ProjectOptions(
        cvMethod=CVMethod.RandomCV,
        validationType=dr.enums.VALIDATION_TYPE.CV,
        reps=None,
        validationPct=None,
        holdoutPct=None,
        metric=dr.enums.ACCURACY_METRIC.RMSE,
    ),
)

batch_prediction_job_name = f"Weekly Batch Prediction Job [{project_name}]"
batch_prediction_job_schedule = cast(
    DatarobotSchedule,
    Schedule(
        minute=[0],
        hour=[0],
        dayOfMonth=["*"],
        month=["*"],
        dayOfWeek=[1],
    ).model_dump(),
)


def ensure_batch_prediction_job(deployment_id: str, dataset_scoring_id: str) -> None:
    """Ensure batch prediction job is configured on a deployment."""
    client = dr.client.get_client()
    get_update_or_create_batch_prediction_job(
        endpoint=client.endpoint,
        token=client.token,
        deployment_id=deployment_id,
        batch_prediction_job=BatchPredictionJobDefinitionsCreate(
            intake_settings=Catalog(
                type="dataset",
                datasetId=dataset_scoring_id,
            ),
            output_settings=LocalFileOutput(
                type="localFile",
            ),
            deploymentId=deployment_id,
        ).model_dump(mode="json"),
        enabled=True,
        name=batch_prediction_job_name,
        schedule=batch_prediction_job_schedule,
    )


def ensure_retraining_policy(
    deployment_id: str,
    calendar_id: str,
    training_dataset_id: str,
    prediction_environment_id: str,
) -> None:
    """Ensure retraining policy is configured on a TS deployment."""
    retraining_policy_settings.timeSeriesOptions = TimeSeriesOptions(
        calendarId=calendar_id
    )
    client = dr.client.get_client()
    get_update_or_create_retraining_policy(
        endpoint=client.endpoint,
        token=client.token,
        deployment_id=deployment_id,
        dataset_id=training_dataset_id,
        prediction_environment_id=prediction_environment_id,
        **retraining_policy_settings.model_dump(mode="json"),
    )


def update_dynamic_deployment_settings(
    deployment_args: DeploymentArgs,
    datetime_partition_column: str,
    date_format: str,
    prediction_interval: int,
) -> None:
    """Dynamically set deployment settings that are dependent on model training"""
    deployment_args.predictions_by_forecast_date_settings = (
        datarobot.DeploymentPredictionsByForecastDateSettingsArgs(
            enabled=True,
            column_name=datetime_partition_column,
            datetime_format=date_format,
        )
    )
    deployment_args.prediction_intervals_settings = (
        datarobot.DeploymentPredictionIntervalsSettingsArgs(
            enabled=True, percentiles=[prediction_interval]
        )
    )
