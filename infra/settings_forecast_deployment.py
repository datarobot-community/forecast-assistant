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
import datarobot as dr
import pulumi_datarobot as datarobot
from datarobot_pulumi_utils.schema.common import Schedule
from datarobot_pulumi_utils.schema.custom_models import DeploymentArgs
from datarobot_pulumi_utils.schema.training import (
    ActionType,
    AutopilotOptions,
    CVMethod,
    DeploymentRetrainingPolicyArgs,
    FeatureListStrategy,
    ModelSelectionStrategy,
    ProjectOptions,
    ProjectOptionsStrategy,
    RetrainingTrigger,
    TriggerType,
)

from .settings_main import default_prediction_server_id, project_name


def get_deployment_args(
    datetime_partition_column: str,
    date_format: str,
    prediction_interval: int,
) -> DeploymentArgs:
    return DeploymentArgs(
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
                min_computes=0, max_computes=1
            )
        ),
        predictions_data_collection_settings=datarobot.DeploymentPredictionsDataCollectionSettingsArgs(
            enabled=True
        ),
        drift_tracking_settings=datarobot.DeploymentDriftTrackingSettingsArgs(
            feature_drift_enabled=True, target_drift_enabled=True
        ),
        predictions_by_forecast_date_settings=(
            datarobot.DeploymentPredictionsByForecastDateSettingsArgs(
                enabled=True,
                column_name=datetime_partition_column,
                datetime_format=date_format,
            )
        ),
        prediction_intervals_settings=(
            datarobot.DeploymentPredictionIntervalsSettingsArgs(
                enabled=True, percentiles=[prediction_interval]
            )
        ),
    )


retraining_policy_settings = DeploymentRetrainingPolicyArgs(
    resource_name=f"Retrain on Accuracy Decline [{project_name}]",
    description="",
    action=ActionType.MODEL_REPLACEMENT,
    autopilot_options=AutopilotOptions(
        mode=dr.enums.AUTOPILOT_MODE.QUICK,
        blend_best_models=False,
        shap_only_mode=False,
        run_leakage_removed_feature_list=True,
    ),
    trigger=RetrainingTrigger(
        type=TriggerType.ACCURACY_DECLINE,
        schedule=Schedule(
            minutes=["0"],
            hours=["0"],
            day_of_months=["*"],
            months=["*"],
            day_of_weeks=["*"],
        ),
        status_declines_to_warning=True,
        status_declines_to_failing=False,
        status_still_in_decline=False,
    ),
    project_options_strategy=ProjectOptionsStrategy.SAME_AS_CHAMPION,
    feature_list_strategy=FeatureListStrategy.INFORMATIVE_FEATURES,
    model_selection_strategy=ModelSelectionStrategy.AUTOPILOT_RECOMMENDED,
    project_options=ProjectOptions(
        cv_method=CVMethod.RANDOM_CV,
        validation_type=dr.enums.VALIDATION_TYPE.CV,
        reps=None,
        validation_pct=None,
        holdout_pct=None,
        metric=dr.enums.ACCURACY_METRIC.RMSE,
    ),
)

batch_prediction_job_name = f"Weekly Batch Prediction Job [{project_name}]"
batch_prediction_job_schedule = Schedule(
    minutes=["0"],
    hours=["0"],
    day_of_months=["*"],
    months=["*"],
    day_of_weeks=["1"],
).model_dump()
