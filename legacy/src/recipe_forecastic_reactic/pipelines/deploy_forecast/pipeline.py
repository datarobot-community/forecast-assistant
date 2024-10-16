# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from kedro.pipeline import node, Pipeline
from kedro.pipeline.modular_pipeline import pipeline

import datarobot as dr

from datarobotx.idp.autopilot import get_or_create_autopilot_run
from datarobotx.idp.calendars import get_or_create_calendar_dataset_from_country_code
from datarobotx.idp.deployments import (
    get_replace_or_create_deployment_from_registered_model,
)

from datarobotx.idp.registered_model_versions import (
    get_or_create_registered_leaderboard_model_version,
)

from .nodes import (
    get_date_format,
    get_most_important_features,
    get_what_if_features,
    get_timestep_settings,
    input_urls,
)


def create_pipeline(**kwargs) -> Pipeline:
    nodes = [
        node(
            name="generate_calendar",
            func=get_or_create_calendar_dataset_from_country_code,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "name": "params:project.calendar.name",
                "country_code": "params:project.calendar.country_code",
                "start_date": "params:project.calendar.start_date",
                "end_date": "params:project.calendar.end_date",
            },
            outputs="calendar_id",
        ),
        node(
            name="make_autopilot_run",
            func=get_or_create_autopilot_run,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "name": "params:project.name",
                "dataset_id": "training_dataset_id",
                "analyze_and_model_config": "params:project.analyze_and_model_config",
                "datetime_partitioning_config": "params:project.datetime_partitioning_config",
                "feature_settings_config": "params:project.feature_settings_config",
                "advanced_options_config": "params:project.advanced_options_config",
                "use_case": "use_case_id",
                "calendar_id": "calendar_id",
            },
            outputs="project_id",
        ),
        node(
            name="get_recommended_model",
            func=lambda project_id: dr.ModelRecommendation.get(project_id).model_id,
            inputs="project_id",
            outputs="recommended_model_id",
        ),
        node(
            name="get_recommended_model_name",
            func=lambda project_id, model_id: dr.Model.get(
                project_id, model_id
            ).model_type,
            inputs=["project_id", "recommended_model_id"],
            outputs="recommended_model_name",
        ),
        node(
            name="make_registered_model_name",
            func=lambda registered_model_name,
            forecast_window_start,
            forecast_window_end: (
                registered_model_name
                + " ("
                + str(forecast_window_start)
                + ", "
                + str(forecast_window_end)
                + ")"
            ),
            inputs={
                "registered_model_name": "params:registered_model.name",
                "forecast_window_start": "params:project.datetime_partitioning_config.forecast_window_start",
                "forecast_window_end": "params:project.datetime_partitioning_config.forecast_window_end",
            },
            outputs="modified_registered_model_name",
        ),
        node(
            name="make_registered_model",
            func=get_or_create_registered_leaderboard_model_version,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "model_id": "recommended_model_id",
                "registered_model_name": "modified_registered_model_name",
            },
            outputs="registered_model_version_id",
        ),
        node(
            name="make_deployment",
            func=get_replace_or_create_deployment_from_registered_model,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "registered_model_version_id": "registered_model_version_id",
                "registered_model_name": "modified_registered_model_name",
                "label": "params:deployment.label",
                "description": "params:deployment.description",
                "prediction_environment_id": "params:credentials.datarobot.prediction_environment_id",
            },
            outputs="deployment_id",
        ),
        node(
            name="get_most_important_features",
            func=get_most_important_features,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "project_id": "project_id",
                "model_id": "recommended_model_id",
                "minimum_importance": "params:feature_importance.minimum_importance",
                "max_wait": "params:feature_importance.max_wait",
            },
            outputs="important_features",
        ),
        node(
            name="get_what_if_features",
            func=get_what_if_features,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "project_id": "project_id",
                "model_id": "recommended_model_id",
                "feature_settings_config": "params:project.feature_settings_config",
            },
            outputs="what_if_features",
        ),
        node(
            name="get_date_format",
            func=get_date_format,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "project_id": "project_id",
            },
            outputs="date_format",
        ),
        node(
            name="get_timestep_settings",
            func=get_timestep_settings,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "project_id": "project_id",
                "datetime_partition_column": "params:project.datetime_partitioning_config.datetime_partition_column",
            },
            outputs="timestep_settings",
        ),
        node(
            name="get_urls",
            func=input_urls,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "scoring_dataset_id": "scoring_dataset_id",
                "project_id": "project_id",
                "model_id": "recommended_model_id",
                "deployment_id": "deployment_id",
            },
            outputs="app_urls",
        ),
    ]
    pipeline_inst = pipeline(nodes)
    return pipeline(
        pipeline_inst,
        namespace="deploy_forecast",
        parameters={
            "params:credentials.datarobot.endpoint": "params:credentials.datarobot.endpoint",
            "params:credentials.datarobot.api_token": "params:credentials.datarobot.api_token",
            "params:credentials.datarobot.prediction_environment_id": "params:credentials.datarobot.prediction_environment_id",
        },
        inputs={"use_case_id", "training_dataset_id", "scoring_dataset_id"},
        outputs={
            "project_id",
            "recommended_model_id",
            "recommended_model_name",
            "deployment_id",
            "date_format",
            "important_features",
            "what_if_features",
            "timestep_settings",
            "app_urls",
        },
    )
