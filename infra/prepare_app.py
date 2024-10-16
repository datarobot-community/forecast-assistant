# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from typing import Any, Dict, List, Optional

import datarobot as dr

from forecastic.schema import DynamicAppSettings, FeatureSettingConfig

from .settings_app_infra import _application_path, app_name, minimum_feature_importance
from .settings_deploy_forecasts import (
    autopilotrun_args,
    prediction_interval,
)


def get_most_important_features(
    project_id: str,
    model_id: str,
    minimum_importance: float = 0.03,
    max_wait: int = 600,
) -> List[dict[str, Any]]:
    """Get the most important features for the model.

    Parameters
    ----------
    max_features : int
        The maximum number of features to return
    max_wait : int
        The maximum time to wait for the feature impact to be calculated
    """

    model = dr.Model.get(model_id=model_id, project=project_id)  # type: ignore[attr-defined]
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
    project_id: str,
    model_id: str,
    feature_settings_config: Optional[List[FeatureSettingConfig]] = None,
) -> list[dict[str, Any]]:
    """Get whatif features.

    Only returns categorical and numeric known in advance features.
    Categories are returned with selectable options.

    Parameters
    ----------
    feature_settings_config : Optional[List[Dict[str, Any]]]
        Known in advance features
    """

    if not feature_settings_config:
        return []

    project = dr.Project.get(project_id)  # type: ignore[attr-defined]
    model = dr.Model.get(project=project_id, model_id=model_id)  # type: ignore[attr-defined]
    dataset = project.get_dataset()
    if dataset is None:
        raise ValueError("Dataset not found")
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
            feature.known_in_advance
            and feature.feature_name in model_features
            and feature.feature_name in allowed_features
        ):
            append_feature = feature.model_dump(mode="json")
            if feature.feature_name in categoricals:
                append_feature["values"] = list(
                    dataframe[feature.feature_name].unique()
                )

            whatif_features.append(append_feature)

    return whatif_features


def get_timestep_settings(
    project_id: str,
    datetime_partition_column: str,
) -> Dict[str, Any]:
    """Get window basis unit and interval from timeseries project

    Returns
    -------
    Dict[str, Any]
        Time unit and step
    """

    client = dr.client.get_client()

    url = f"projects/{project_id}/features/{datetime_partition_column}/multiseriesProperties"
    response = client.get(url).json()
    timestep_settings: dict[str, Any] = response["detectedMultiseriesIdColumns"][0]
    del timestep_settings["multiseriesIdColumns"]

    return timestep_settings


def input_urls(
    scoring_dataset_id: str,
    project_id: str,
    model_id: str,
    # deployment_id: Output[str],
) -> dict[str, str]:
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

    client = dr.client.get_client()
    urls = {}
    base_url = client.endpoint[: client.endpoint.find("/api")]
    urls["dataset_url"] = urljoin(base_url, f"ai-catalog/{scoring_dataset_id}")
    urls["model_url"] = urljoin(base_url, f"projects/{project_id}/models/{model_id}")
    return urls


def prepare_app_settings(
    project_id: str, recommended_model_id: str, scoring_dataset_id: str
) -> DynamicAppSettings:
    def make_recommended_model_name(project_id: str, model_id: str) -> str:
        return str(dr.Model.get(project_id, model_id).model_type)  # type: ignore[attr-defined]

    recommended_model_name = make_recommended_model_name(
        project_id=project_id, model_id=recommended_model_id
    )

    important_features = get_most_important_features(
        project_id=project_id,
        model_id=recommended_model_id,
        minimum_importance=minimum_feature_importance,
    )

    what_if_features = get_what_if_features(
        project_id=project_id,
        model_id=recommended_model_id,
        feature_settings_config=autopilotrun_args.feature_settings_config,
    )

    date_format = str(dr.DatetimePartitioning.get(project_id=project_id).date_format)

    timestep_settings = get_timestep_settings(
        project_id=project_id,
        datetime_partition_column=autopilotrun_args.datetime_partitioning_config.datetime_partition_column,  # type: ignore[union-attr]
    )

    app_urls = input_urls(
        scoring_dataset_id=scoring_dataset_id,
        project_id=project_id,
        model_id=recommended_model_id,
    )

    dynamic_app_settings = DynamicAppSettings(
        important_features=important_features,
        what_if_features=what_if_features,
        timestep_settings=timestep_settings,
        app_urls=app_urls,
        application_name=app_name,
        date_format=date_format,
        datetime_partition_column=autopilotrun_args.datetime_partitioning_config.datetime_partition_column,  # type: ignore[union-attr]
        model_id=recommended_model_id,
        feature_derivation_window_end=autopilotrun_args.datetime_partitioning_config.feature_derivation_window_end,  # type: ignore[union-attr]
        feature_derivation_window_start=autopilotrun_args.datetime_partitioning_config.feature_derivation_window_start,  # type: ignore[union-attr]
        forecast_window_end=autopilotrun_args.datetime_partitioning_config.forecast_window_end,  # type: ignore[union-attr]
        forecast_window_start=autopilotrun_args.datetime_partitioning_config.forecast_window_start,  # type: ignore[union-attr]
        model_name=recommended_model_name,
        multiseries_id_column=autopilotrun_args.datetime_partitioning_config.multiseries_id_columns[  # type: ignore[index,union-attr]
            0
        ],
        prediction_interval=prediction_interval,
        project_id=project_id,
        scoring_dataset_id=scoring_dataset_id,
        target=autopilotrun_args.analyze_and_model_config.target,  # type: ignore[union-attr]
    )
    return dynamic_app_settings


def gather_assets(
    project_id: str,
    recommended_model_id: str,
    scoring_dataset_id: str,
) -> list[tuple[str, str]]:
    dynamic_app_settings = prepare_app_settings(
        project_id=project_id,
        recommended_model_id=recommended_model_id,
        scoring_dataset_id=scoring_dataset_id,
    )

    dynamic_app_settings_name = "dynamic_app_settings.json"
    (_application_path / dynamic_app_settings_name).write_text(
        dynamic_app_settings.model_dump_json(indent=4), encoding="utf-8"
    )
    files = [
        (str(f), str(f.relative_to(_application_path)))
        for f in _application_path.glob("**/*")
        if f.is_file()
    ] + [
        ("forecastic/__init__.py", "forecastic/__init__.py"),
        ("forecastic/settings_app.py", "forecastic/settings_app.py"),
        ("forecastic/schema.py", "forecastic/schema.py"),
        ("forecastic/predict.py", "forecastic/predict.py"),
        ("forecastic/deployments.py", "forecastic/deployments.py"),
        ("forecastic/credentials.py", "forecastic/credentials.py"),
    ]
    return files
