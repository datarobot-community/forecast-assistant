# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from kedro.pipeline import node, Pipeline
from kedro.pipeline.modular_pipeline import pipeline

from datarobotx.idp.datasets import get_or_create_dataset_from_df
from datarobotx.idp.use_cases import get_or_create_use_case

from .nodes import test_parameter_names_are_valid


def create_pipeline(**kwargs) -> Pipeline:
    nodes = [
        node(
            name="training_parameter_names_are_valid",
            func=test_parameter_names_are_valid,
            inputs={
                "dataset": "training_data",
                "target": "params:project.analyze_and_model_config.target",
                "datetime_partition_column": "params:project.datetime_partitioning_config.datetime_partition_column",
                "multiseries_id_columns": "params:project.datetime_partitioning_config.multiseries_id_columns",
                "feature_settings_config": "params:project.feature_settings_config",
            },
            outputs=None,
        ),
        node(
            name="scoring_parameter_names_are_valid",
            func=test_parameter_names_are_valid,
            inputs={
                "dataset": "scoring_data",
                "target": "params:project.analyze_and_model_config.target",
                "datetime_partition_column": "params:project.datetime_partitioning_config.datetime_partition_column",
                "multiseries_id_columns": "params:project.datetime_partitioning_config.multiseries_id_columns",
                "feature_settings_config": "params:project.feature_settings_config",
            },
            outputs=None,
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
            name="load_training_dataset",
            func=get_or_create_dataset_from_df,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "name": "params:training_dataset_name",
                "use_cases": "use_case_id",
                "data_frame": "training_data",
            },
            outputs="training_dataset_id",
        ),
        node(
            name="load_scoring_dataset",
            func=get_or_create_dataset_from_df,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "name": "params:scoring_dataset_name",
                "use_cases": "use_case_id",
                "data_frame": "scoring_data",
            },
            outputs="scoring_dataset_id",
        ),
        node(
            name="define_dataset_type",
            func=lambda: "from_file",
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
