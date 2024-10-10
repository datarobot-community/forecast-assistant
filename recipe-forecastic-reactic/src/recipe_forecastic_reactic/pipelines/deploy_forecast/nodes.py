# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from typing import Any, Dict, List


def get_most_important_features(
    endpoint: str,
    token: str,
    project_id: str,
    model_id: str,
    minimum_importance: float = 0.03,
    max_wait: int = 600,
) -> List[str]:
    """Get the most important features for the model.

    Parameters
    ----------
    max_features : int
        The maximum number of features to return
    max_wait : int
        The maximum time to wait for the feature impact to be calculated
    """

    import datarobot as dr

    dr.Client(endpoint=endpoint, token=token)

    model = dr.Model.get(model_id=model_id, project=project_id)
    feature_impact = model.get_or_request_feature_impact(max_wait=max_wait)

    return [
        {
            "featureName": feature["featureName"],
            "impactNormalized": feature["impactNormalized"],
        }
        for feature in feature_impact
        if feature["impactNormalized"] > minimum_importance
    ]


def get_what_if_features(
    endpoint: str,
    token: str,
    project_id: str,
    model_id: str,
    feature_settings_config: List[Dict[str, Any]] = None,
):
    """Get whatif features.

    Only returns categorical and numeric known in advance features.
    Categories are returned with selectable options.

    Parameters
    ----------
    feature_settings_config : Optional[List[Dict[str, Any]]]
        Known in advance features
    """

    import datarobot as dr

    dr.Client(endpoint=endpoint, token=token)

    if not feature_settings_config:
        return []

    project = dr.Project.get(project_id)
    model = dr.Model.get(project=project_id, model_id=model_id)
    dataset = project.get_dataset()
    model_features = set(model.get_features_used())
    feature_types = dataset.get_all_features()
    dataframe = dataset.get_as_dataframe()

    numerics = set([i.name for i in feature_types if i.feature_type == "Numeric"])
    categoricals = set(
        [i.name for i in feature_types if i.feature_type == "Categorical"]
    )
    allowed_features = numerics.union(categoricals)

    whatif_features = []
    for feature in feature_settings_config:
        if (
            feature.get("known_in_advance", False)
            and feature["feature_name"] in model_features
            and feature["feature_name"] in allowed_features
        ):
            append_feature = feature
            if feature["feature_name"] in categoricals:
                append_feature["values"] = list(
                    dataframe[feature["feature_name"]].unique()
                )

            whatif_features.append(feature)

    return whatif_features


def get_date_format(
    endpoint: str,
    token: str,
    project_id: str,
):
    "Get date format for project"
    import datarobot as dr

    client = dr.Client(endpoint=endpoint, token=token)
    url = "projects/{}/datetimePartitioning".format(project_id)
    response = client.get(url).json()
    return response["dateFormat"]


def get_timestep_settings(
    endpoint: str,
    token: str,
    project_id: str,
    datetime_partition_column: str,
) -> Dict[str, Any]:
    """Get window basis unit and interval from timeseries project

    Returns
    -------
    Dict[str, Any]
        Time unit and step
    """
    import datarobot as dr

    client = dr.Client(endpoint=endpoint, token=token)

    url = f"projects/{project_id}/features/{datetime_partition_column}/multiseriesProperties"
    response = client.get(url).json()
    timestep_settings = response["detectedMultiseriesIdColumns"][0]
    del timestep_settings["multiseriesIdColumns"]

    return timestep_settings


def input_urls(
    endpoint: str,
    scoring_dataset_id: str,
    project_id: str,
    model_id: str,
    deployment_id: str,
):
    """Add urls to DataRobot Assets

    Parameters
    ----------
    scoring_dataset_id : str
        DataRobot id of the scoring dataset
    project_id : str
        DataRobot id of the project
    model_id : str
        DataRobot id of the top model in project
    deployment_id : str
        DataRobot id of the deployment
    """
    from urllib.parse import urljoin

    urls = {}
    base_url = endpoint[: endpoint.find("/api")]
    urls["dataset_url"] = urljoin(base_url, f"ai-catalog/{scoring_dataset_id}")
    urls["model_url"] = urljoin(base_url, f"projects/{project_id}/models/{model_id}")
    urls["deployment_url"] = urljoin(base_url, f"deployments/{deployment_id}")
    return urls
