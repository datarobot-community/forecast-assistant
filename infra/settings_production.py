# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from typing import Any

import datarobot as dr
from datarobotx.idp.batch_predictions import get_update_or_create_batch_prediction_job
from datarobotx.idp.retraining_policies import get_update_or_create_retraining_policy

from infra.common.schema_batch_predictions import (
    BatchPredictionJobDefinitionsCreate,
    Catalog,
    LocalFileOutput,
)
from infra.common.schema_retraining import (
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


def get_retraining_policy(calendar_id: str) -> RetrainingPolicyCreate:
    return RetrainingPolicyCreate(
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
        timeSeriesOptions=TimeSeriesOptions(calendarId=calendar_id),
    )


batch_prediction_job_name = "Weekly Batch Prediction Job"
batch_prediction_job_schedule = Schedule(
    minute=[0],
    hour=[0],
    dayOfMonth=["*"],
    month=["*"],
    dayOfWeek=[1],
).model_dump(mode="json")


def get_batch_prediction_settings(
    deployment_id: str,
    scoring_dataset_id: str,
) -> dict[str, Any]:
    return BatchPredictionJobDefinitionsCreate(
        num_concurrent=3,
        intake_settings=Catalog(
            type="dataset",
            datasetId=scoring_dataset_id,
        ),
        output_settings=LocalFileOutput(
            type="localFile",
        ),
        deploymentId=deployment_id,
    ).model_dump(mode="json")


def update_batch_prediction_job(deployment_id: str, dataset_scoring_id: str) -> None:
    batch_prediction_job = get_batch_prediction_settings(
        deployment_id=deployment_id, scoring_dataset_id=dataset_scoring_id
    )
    client = dr.client.get_client()

    get_update_or_create_batch_prediction_job(
        endpoint=client.endpoint,
        token=client.token,
        deployment_id=deployment_id,
        batch_prediction_job=batch_prediction_job,
        enabled=True,
        name=batch_prediction_job_name,
        schedule=batch_prediction_job_schedule,
    )


def update_retraining_policy(
    deployment_id: str, calendar_id: str, training_dataset_id: str
) -> None:
    retraining_policy = get_retraining_policy(
        calendar_id=calendar_id,
    )
    client = dr.client.get_client()
    get_update_or_create_retraining_policy(
        endpoint=client.endpoint,
        token=client.token,
        deployment_id=deployment_id,
        dataset_id=training_dataset_id,
        **retraining_policy.model_dump(mode="json"),
    )


def auto_stopping_app(app_id: str) -> None:
    dr.client.get_client().patch(
        f"customApplications/{app_id}/",
        json={"allowAutoStopping": True},
    )
