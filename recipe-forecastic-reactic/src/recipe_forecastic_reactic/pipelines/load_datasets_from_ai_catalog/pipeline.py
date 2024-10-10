# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from kedro.pipeline import node, Pipeline
from kedro.pipeline.modular_pipeline import pipeline

from datarobotx.idp.use_cases import get_or_create_use_case

from .nodes import add_datasets_to_use_case, test_parameter_names_are_valid


def create_pipeline(**kwargs) -> Pipeline:
    nodes = [
        node(
            name="training_parameter_names_are_valid",
            func=test_parameter_names_are_valid,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "dataset_id": "params:training_dataset_id",
                "target": "params:project.analyze_and_model_config.target",
                "datetime_partition_column": "params:project.datetime_partitioning_config.datetime_partition_column",
                "multiseries_id_columns": "params:project.datetime_partitioning_config.multiseries_id_columns",
                "feature_settings_config": "params:project.feature_settings_config",
            },
            outputs="training_validity_check",
        ),
        node(
            name="scoring_parameter_names_are_valid",
            func=test_parameter_names_are_valid,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "dataset_id": "params:scoring_dataset_id",
                "target": "params:project.analyze_and_model_config.target",
                "datetime_partition_column": "params:project.datetime_partitioning_config.datetime_partition_column",
                "multiseries_id_columns": "params:project.datetime_partitioning_config.multiseries_id_columns",
                "feature_settings_config": "params:project.feature_settings_config",
            },
            outputs="scoring_validity_check",
        ),
        node(
            name="make_datarobot_use_case",
            func=get_or_create_use_case,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "name": "params:use_case.name",
                "description": "params:use_case.description",
            },
            outputs="use_case_id",
        ),
        node(
            name="training_param_to_catalog",
            func=lambda x, is_valid: is_valid and x,
            inputs=["params:training_dataset_id", "training_validity_check"],
            outputs="training_dataset_id",
        ),
        node(
            name="scoring_param_to_catalog",
            func=lambda x, is_valid: is_valid and x,
            inputs=["params:scoring_dataset_id", "scoring_validity_check"],
            outputs="scoring_dataset_id",
        ),
        node(
            name="add_datasets_to_use_case",
            func=add_datasets_to_use_case,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "use_case_id": "use_case_id",
                "training_dataset_id": "training_dataset_id",
                "scoring_dataset_id": "scoring_dataset_id",
            },
            outputs=None,
        ),
        node(
            name="define_dataset_type",
            func=lambda: "from_ai_catalog",
            inputs=None,
            outputs="dataset_type",
        ),
    ]
    pipeline_inst = pipeline(nodes)
    return pipeline(
        pipeline_inst,
        namespace="load_datasets",
        parameters={
            "params:credentials.datarobot.endpoint": "params:credentials.datarobot.endpoint",
            "params:credentials.datarobot.api_token": "params:credentials.datarobot.api_token",
            "params:project.analyze_and_model_config.target": "params:deploy_forecast.project.analyze_and_model_config.target",
            "params:project.datetime_partitioning_config.multiseries_id_columns": "params:deploy_forecast.project.datetime_partitioning_config.multiseries_id_columns",
            "params:project.datetime_partitioning_config.datetime_partition_column": "params:deploy_forecast.project.datetime_partitioning_config.datetime_partition_column",
            "params:project.feature_settings_config": "params:deploy_forecast.project.feature_settings_config",
        },
        outputs={
            "use_case_id",
            "training_dataset_id",
            "scoring_dataset_id",
            "dataset_type",
        },
    )
