# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from __future__ import annotations
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


def ensure_deployment_settings(
    endpoint: str,
    token: str,
    deployment_id: str,
    datetime_partitioning_column: str,
    prediction_interval: int,
    date_format: str,
    association_id: Optional[str] = None,
) -> None:
    """Ensure deployment settings are properly configured.

    Parameters
    ----------
    datetime_partitioning_column: str
        The datetime partitioning column
    prediction_interval: int
        The prediction interval to set for the deployment
    date_format: str
        The date format derived from the dataset
    association_id: Optional[str]
        The association id, if any.
        When not set, the association id is auto-generated
    """
    import datarobot as dr

    deployment_settings_url = f"deployments/{deployment_id}/settings/"
    client = dr.Client(endpoint=endpoint, token=token)

    deployment = dr.Deployment.get(deployment_id)

    deployment.update_predictions_data_collection_settings(enabled=True)
    deployment.update_drift_tracking_settings(
        target_drift_enabled=True, feature_drift_enabled=True
    )

    deployment.update_prediction_intervals_settings(percentiles=[prediction_interval])

    datetime_partition_column = datetime_partitioning_column + " (actual)"
    request_body = {
        "predictionsByForecastDate": {
            "enabled": True,
            "columnName": datetime_partition_column,
            "datetimeFormat": date_format,
        },
        "automaticActuals": {"enabled": True},
    }

    if association_id is None:
        request_body["associationId"] = {
            "columnNames": ["auto_generated_id"],
            "requiredInPredictionRequests": False,
            "autoGenerateId": True,
        }
    else:
        request_body["associationId"] = {
            "columnNames": [association_id],
            "requiredInPredictionRequests": False,
            "autoGenerateId": False,
        }

    try:
        client.patch(deployment_settings_url, json=request_body)
    # Remove v2 on error
    except dr.errors.ClientError:
        request_body["predictionsByForecastDate"]["datetimeFormat"] = "v2" + date_format
        client.patch(deployment_settings_url, json=request_body)

    return "True"


def get_datarobot_prediction_server(
    endpoint: str,
    token: str,
    deployment_id: str,
    prediction_environment_id: str,
    max_explanations: int,
) -> Dict[str, str]:
    """Get the DataRobot prediction server key.

    Returns:
    --------
    Dict[str, str]:
        DataRobot prediction server settings for the application
    """
    from urllib.parse import urljoin

    import datarobot as dr

    dr.Client(endpoint=endpoint, token=token)
    prediction_server = next(
        i for i in dr.PredictionServer.list() if i.id == prediction_environment_id
    )
    prediction_server_data = prediction_server.__dict__.copy()
    prediction_server_data["prediction_request_url"] = urljoin(
        prediction_server.url,
        f"predApi/v1.0/deployments/{deployment_id}/predictions?maxExplanations={max_explanations}",
    )
    return prediction_server_data


def test_deployment_predictions(
    endpoint: str,
    token: str,
    prediction_server: Dict[str, str],
    scoring_dataset_id: pd.DataFrame,
    settings_are_computed: str,
):
    """Test the deployment predictions.

    Parameters
    ----------
    prediction_server : Dict[str, str]
        The prediction server
    scoring_data_sample : pd.DataFrame
        The scoring data sample
    settings_are_computed : str
        Whether the settings are computed.
        Ensures that the deployment is properly configured
    """
    import logging

    import datarobot as dr
    import requests

    logger = logging.getLogger(__name__)

    dr.Client(endpoint=endpoint, token=token)

    assert settings_are_computed

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "datarobot-key": prediction_server["datarobot_key"],
    }

    data = (
        dr.Dataset.get(scoring_dataset_id).get_as_dataframe().to_json(orient="records")
    )
    url = prediction_server["prediction_request_url"]
    response = requests.post(url, headers=headers, data=data)
    try:
        response.raise_for_status()
        logger.info(
            "Success! The deployment can make predicitons using the provided scoring data"
        )
    except requests.exceptions.HTTPError:
        print(response.json()[:5])
        response.raise_for_status()

    return "True"


def setup_batch_prediction_job_definition(
    endpoint: str,
    token: str,
    deployment_id: str,
    dataset_id: str,
    enabled: bool,
    batch_prediction_job: dict,
    name: str,
    schedule: Optional[str | None],
) -> str:
    """Set up BatchPredictionJobDefinition for deployment to enable informed retraining.

    enabled: bool
        Whether or not the definition should be active on a scheduled basis. If True, `schedule` is required
    name: str
        * Must be unique to your organization *
        Name of batch prediction job definition. If given the name of an existing definition within the supplied
        deployment (according to deployment_id), this function will overwrite that existing definition with parameters
        specified in this function (batch_prediction_job, enabled, schedule).
    schedule : dict (optional)
        The ``schedule`` payload defines at what intervals the job should run, which can be
        combined in various ways to construct complex scheduling terms if needed. In all of
        the elements in the objects, you can supply either an asterisk ``["*"]`` denoting
        "every" time denomination or an array of integers (e.g. ``[1, 2, 3]``) to define
        a specific interval.
    """

    from datarobotx.idp.batch_predictions import (
        get_update_or_create_batch_prediction_job,
    )

    batch_prediction_job["intake_settings"]["datasetId"] = dataset_id
    batch_prediction_job["deploymentId"] = deployment_id

    return get_update_or_create_batch_prediction_job(
        endpoint=endpoint,
        token=token,
        deployment_id=deployment_id,
        batch_prediction_job=batch_prediction_job,
        enabled=enabled,
        name=name,
        schedule=schedule,
    )
