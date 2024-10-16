# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

import datarobot as dr
import pulumi_datarobot as datarobot

from forecastic.schema import FeatureSettingConfig

from .common.schema import (
    AdvancedOptionsArgs,
    AnalyzeAndModelArgs,
    AutopilotRunArgs,
    CalendarArgs,
    DatetimePartitioningArgs,
    DeploymentArgs,
    RegisteredModelArgs,
)
from .settings_main import default_prediction_server_id, project_name

prediction_interval = 80

calendar_args = CalendarArgs(
    country_code="US",
    name=f"Calendar [{project_name}]",
    start_date="2012-01-01",
    end_date="2022-01-01",
)
autopilotrun_args = AutopilotRunArgs(
    name=f"Forecastic Project [{project_name}]",
    advanced_options_config=AdvancedOptionsArgs(seed=42),
    analyze_and_model_config=AnalyzeAndModelArgs(
        metric="RMSE",
        mode=dr.enums.AUTOPILOT_MODE.QUICK,
        target="Sales",
        worker_count=-1,
    ),
    datetime_partitioning_config=DatetimePartitioningArgs(
        datetime_partition_column="Date",
        multiseries_id_columns=["Store"],
        use_time_series=True,
        feature_derivation_window_start=-35,
        feature_derivation_window_end=0,
        forecast_window_start=1,
        forecast_window_end=30,
    ),
    feature_settings_config=[
        FeatureSettingConfig(feature_name="Store_Size", known_in_advance=True),
        FeatureSettingConfig(feature_name="Marketing", known_in_advance=True),
        FeatureSettingConfig(feature_name="TouristEvent", known_in_advance=True),
    ],
)


def get_deployment_args(project_id: str) -> DeploymentArgs:
    date_format = str(dr.DatetimePartitioning.get(project_id=project_id).date_format)
    deployment_args = DeploymentArgs(
        resource_name="deployment-forecasting",
        label=f"Forecastic Deployment [{project_name}]",
        association_id_settings=datarobot.DeploymentAssociationIdSettingsArgs(
            column_names=["association_id"],
            auto_generate_id=False,
            required_in_prediction_requests=False,
        ),
        predictions_settings=None
        if default_prediction_server_id is not None
        else datarobot.DeploymentPredictionsSettingsArgs(
            min_computes=0, max_computes=1, real_time=True
        ),
        prediction_intervals_settings=datarobot.DeploymentPredictionIntervalsSettingsArgs(
            enabled=True, percentiles=[prediction_interval]
        ),
        predictions_data_collection_settings=datarobot.DeploymentPredictionsDataCollectionSettingsArgs(
            enabled=True
        ),
        drift_tracking_settings=datarobot.DeploymentDriftTrackingSettingsArgs(
            feature_drift_enabled=True, target_drift_enabled=True
        ),
        predictions_by_forecast_date_settings=datarobot.DeploymentPredictionsByForecastDateSettingsArgs(
            enabled=True,
            column_name=f"{autopilotrun_args.datetime_partitioning_config.datetime_partition_column} (actual)",  # type: ignore[union-attr]
            datetime_format=f"{date_format}",
        ),
    )
    return deployment_args


registered_model_args = RegisteredModelArgs(
    resource_name="registered-model-forecasting",
    name=f"Forecastic Registered Model [{project_name}]",
)
