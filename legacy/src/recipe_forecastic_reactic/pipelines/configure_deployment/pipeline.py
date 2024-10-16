# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from kedro.pipeline import node, Pipeline
from kedro.pipeline.modular_pipeline import pipeline

from datarobotx.idp.retraining_policies import get_update_or_create_retraining_policy

from .nodes import (
    ensure_deployment_settings,
    get_datarobot_prediction_server,
    setup_batch_prediction_job_definition,
    test_deployment_predictions,
)


def create_pipeline(**kwargs) -> Pipeline:
    nodes = [
        node(
            name="ensure_deployment_settings",
            func=ensure_deployment_settings,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "deployment_id": "deployment_id",
                "datetime_partitioning_column": "params:project.datetime_partitioning_config.datetime_partition_column",
                "prediction_interval": "params:prediction_interval",
                "association_id": "params:deployment.association_id_column_name",
                "date_format": "date_format",
            },
            outputs="settings_are_computed",
        ),
        node(
            name="get_datarobot_prediction_server",
            func=get_datarobot_prediction_server,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "deployment_id": "deployment_id",
                "prediction_environment_id": "params:credentials.datarobot.prediction_environment_id",
                "max_explanations": "params:max_explanations",
            },
            outputs="prediction_server",
        ),
        node(
            name="test_model_can_predict_things",
            func=test_deployment_predictions,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "prediction_server": "prediction_server",
                "scoring_dataset_id": "scoring_dataset_id",
                "settings_are_computed": "settings_are_computed",
            },
            outputs="predictions_are_working",
            tags=["checkpoint"],
        ),
        node(
            name="set_up_batch_prediction_job",
            func=setup_batch_prediction_job_definition,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "deployment_id": "deployment_id",
                "dataset_id": "scoring_dataset_id",
                "enabled": "params:batch_prediction_job_definition.enabled",
                "name": "params:batch_prediction_job_definition.name",
                "batch_prediction_job": "params:batch_prediction_job_definition.batch_prediction_job",
                "schedule": "params:batch_prediction_job_definition.schedule",
            },
            outputs="job_definition_id",
        ),
        node(
            name="set_up_retraining_job",
            func=get_update_or_create_retraining_policy,
            inputs={
                "endpoint": "params:credentials.datarobot.endpoint",
                "token": "params:credentials.datarobot.api_token",
                "deployment_id": "deployment_id",
                "name": "params:retraining_policy.name",
                "dataset_id": "training_dataset_id",
                "autopilotOptions": "params:retraining_policy.retraining_settings.autopilotOptions",
                "trigger": "params:retraining_policy.retraining_settings.trigger",
                "projectOptions": "params:retraining_policy.retraining_settings.projectOptions",
                "featureListStrategy": "params:retraining_policy.retraining_settings.featureListStrategy",
                "projectOptionsStrategy": "params:retraining_policy.retraining_settings.projectOptionsStrategy",
                "modelSelectionStrategy": "params:retraining_policy.retraining_settings.modelSelectionStrategy",
                "action": "params:retraining_policy.retraining_settings.action",
                "credential_id": "params:credential_id",
            },
            outputs="retraining_policy_id",
        ),
    ]
    pipeline_inst = pipeline(nodes)
    return pipeline(
        pipeline_inst,
        namespace="configure_deployment",
        parameters={
            "params:credentials.datarobot.endpoint": "params:credentials.datarobot.endpoint",
            "params:credentials.datarobot.api_token": "params:credentials.datarobot.api_token",
            "params:credentials.datarobot.prediction_environment_id": "params:credentials.datarobot.prediction_environment_id",
            "params:deployment.association_id_column_name": "params:deploy_forecast.deployment.association_id_column_name",
            "params:project.datetime_partitioning_config.datetime_partition_column": "params:deploy_forecast.project.datetime_partitioning_config.datetime_partition_column",
        },
        inputs={
            "date_format",
            "deployment_id",
            "training_dataset_id",
            "scoring_dataset_id",
        },
        outputs={"prediction_server", "predictions_are_working"},
    )
