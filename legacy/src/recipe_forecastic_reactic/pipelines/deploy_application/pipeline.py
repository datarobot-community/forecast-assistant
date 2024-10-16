# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.


from kedro.pipeline import Pipeline, node
from kedro.pipeline.modular_pipeline import pipeline

from datarobotx.idp.common.asset_resolver import prepare_yaml_content, merge_asset_paths
from datarobotx.idp.credentials import get_replace_or_create_credential
from datarobotx.idp.custom_application_source import (
    get_or_create_custom_application_source,
)
from datarobotx.idp.custom_application_source_version import (
    get_or_create_custom_application_source_version,
)
from datarobotx.idp.custom_applications import get_replace_or_create_custom_app

from .nodes import (
    ensure_app_settings,
    log_outputs,
)


def create_pipeline(**kwargs) -> Pipeline:
    nodes = [
        node(
            name="make_llm_credential",
            func=get_replace_or_create_credential,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "name": "params:dr_credential.name",
                "credential_type": "params:dr_credential.credential_type",
                "api_token": "params:credentials.azure_openai_llm_credentials.api_key",
            },
            outputs="dr_llm_credential_id",
        ),
        node(
            name="make_llm_runtime_params",
            func=lambda *args: [
                {
                    "field_name": "llm_endpoint",
                    "type": "string",
                    "value": args[0],
                },
                {
                    "field_name": "llm_api_key",
                    "type": "credential",
                    "value": args[1],
                },
                {
                    "field_name": "llm_api_version",
                    "type": "string",
                    "value": args[2],
                },
                {
                    "field_name": "llm_deployment_name",
                    "type": "string",
                    "value": args[3],
                },
            ],
            inputs=[
                "params:credentials.azure_openai_llm_credentials.azure_endpoint",
                "dr_llm_credential_id",
                "params:credentials.azure_openai_llm_credentials.api_version",
                "params:credentials.azure_openai_llm_credentials.deployment_name",
            ],
            outputs="app_runtime_params",
        ),
        node(
            name="make_frontend_config",
            func=prepare_yaml_content,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "application_name": "params:custom_app_name",
                "project_id": "project_id",
                "model_id": "recommended_model_id",
                "model_name": "recommended_model_name",
                "deployment_id": "deployment_id",
                "scoring_dataset_id": "scoring_dataset_id",
                "page_title": "params:page_title",
                "graph_y_axis": "params:graph_y_axis",
                "date_format": "date_format",
                "target": "params:project.analyze_and_model_config.target",
                "datetime_partition_column": "params:project.datetime_partitioning_config.datetime_partition_column",
                "multiseries_id_column": "params:project.datetime_partitioning_config.multiseries_id_columns",
                "feature_derivation_window_start": "params:project.datetime_partitioning_config.feature_derivation_window_start",
                "feature_derivation_window_end": "params:project.datetime_partitioning_config.feature_derivation_window_end",
                "forecast_window_start": "params:project.datetime_partitioning_config.forecast_window_start",
                "forecast_window_end": "params:project.datetime_partitioning_config.forecast_window_end",
                "what_if_features": "what_if_features",
                "prediction_interval": "params:deployment.prediction_interval",
                "important_features": "important_features",
                "timestep_settings": "timestep_settings",
                "app_urls": "app_urls",
                "prediction_server": "prediction_server",
                "predictions_are_working": "predictions_are_working",
                "page_description": "params:react_frontend_params.page_description",
                "filterable_categories": "params:react_frontend_params.filterable_categories",
                "lower_bound_forecast_at_0": "params:streamlit_frontend_params.lower_bound_forecast_at_0",
                "headline_prompt": "params:streamlit_frontend_params.headline_prompt",
            },
            outputs="frontend_config",
        ),
        node(
            name="merge_assets",
            func=merge_asset_paths,
            inputs=["frontend_config", "app_assets"],
            outputs="app_assets_with_parameters",
        ),
        node(
            name="create_custom_application_source",
            func=get_or_create_custom_application_source,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "name": "params:custom_app_name",
            },
            outputs="custom_application_source_id",
        ),
        node(
            name="make_application_source_version",
            func=get_or_create_custom_application_source_version,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "custom_application_source_id": "custom_application_source_id",
                "base_environment_id": "params:base_environment_id",
                "folder_path": "app_assets_with_parameters",
                "name": "params:custom_app_name",
                "runtime_parameter_values": "app_runtime_params",
            },
            outputs="custom_application_source_version_id",
        ),
        node(
            name="deploy_app",
            func=get_replace_or_create_custom_app,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "custom_application_source_version_id": "custom_application_source_version_id",
                "name": "params:custom_app_name",
            },
            outputs="application_id",
        ),
        node(
            name="ensure_app_settings",
            func=ensure_app_settings,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "app_id": "application_id",
                "allow_auto_stopping": "params:allow_auto_stopping",
            },
            outputs=None,
        ),
        node(
            name="log_outputs",
            func=log_outputs,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "project_id": "project_id",
                "model_id": "recommended_model_id",
                "deployment_id": "deployment_id",
                "application_id": "application_id",
                "project_name": "params:project.name",
                "deployment_name": "params:deployment.label",
                "app_name": "params:custom_app_name",
            },
            outputs=None,
        ),
    ]
    pipeline_inst = pipeline(nodes)
    return pipeline(
        pipeline_inst,
        namespace="deploy_application",
        parameters={
            "params:credentials.datarobot.endpoint": "params:credentials.datarobot.endpoint",
            "params:credentials.datarobot.api_token": "params:credentials.datarobot.api_token",
            "params:credentials.azure_openai_llm_credentials.azure_endpoint": "params:credentials.azure_openai_llm_credentials.azure_endpoint",
            "params:credentials.azure_openai_llm_credentials.api_key": "params:credentials.azure_openai_llm_credentials.api_key",
            "params:credentials.azure_openai_llm_credentials.api_version": "params:credentials.azure_openai_llm_credentials.api_version",
            "params:credentials.azure_openai_llm_credentials.deployment_name": "params:credentials.azure_openai_llm_credentials.deployment_name",
            "params:project.name": "params:deploy_forecast.project.name",
            "params:deployment.label": "params:deploy_forecast.deployment.label",
            "params:project.analyze_and_model_config.target": "params:deploy_forecast.project.analyze_and_model_config.target",
            "params:project.datetime_partitioning_config.multiseries_id_columns": "params:deploy_forecast.project.datetime_partitioning_config.multiseries_id_columns",
            "params:project.datetime_partitioning_config.datetime_partition_column": "params:deploy_forecast.project.datetime_partitioning_config.datetime_partition_column",
            "params:project.datetime_partitioning_config.feature_derivation_window_start": "params:deploy_forecast.project.datetime_partitioning_config.feature_derivation_window_start",
            "params:project.datetime_partitioning_config.feature_derivation_window_end": "params:deploy_forecast.project.datetime_partitioning_config.feature_derivation_window_end",
            "params:project.datetime_partitioning_config.forecast_window_start": "params:deploy_forecast.project.datetime_partitioning_config.forecast_window_start",
            "params:project.datetime_partitioning_config.forecast_window_end": "params:deploy_forecast.project.datetime_partitioning_config.forecast_window_end",
            "params:deployment.prediction_interval": "params:configure_deployment.prediction_interval",
        },
        inputs={
            "scoring_dataset_id",
            "project_id",
            "recommended_model_id",
            "recommended_model_name",
            "deployment_id",
            "prediction_server",
            "predictions_are_working",
            "important_features",
            "what_if_features",
            "date_format",
            "timestep_settings",
            "app_urls",
        },
        outputs={
            "application_id",
        },
    )
