# Copyright 2024 DataRobot, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import annotations

from typing import Any, Dict, List, cast

import datarobot as dr
from pydantic import BaseModel, ConfigDict, Field


class FeatureSettingConfig(BaseModel):
    feature_name: str
    known_in_advance: bool | None = None
    do_not_derive: bool | None = None


class WhatIfFeature(FeatureSettingConfig):
    values: List[str] = Field(default_factory=list)


class CategoryFilter(BaseModel):
    column_name: str
    display_name: str


class StaticAppSettings(BaseModel):
    page_title: str
    page_description: str
    graph_y_axis: str
    lower_bound_forecast_at_0: bool
    filterable_categories: List[CategoryFilter]
    headline_prompt: str


class AppSettings(BaseModel):
    """Dynamic, data science settings needed by the application."""

    registered_model_id: str = Field(
        description="ID of the AutoTS registered model to be deployed for forecasting"
    )
    registered_model_version_id: str = Field(
        description=(
            "ID of the AutoTS registered model version to be deployed for forecasting"
        )
    )
    what_if_features: List[WhatIfFeature] = Field(
        description="Features that may be of interest for what if analysis in the front end"
    )
    important_features: List[dict[str, Any]] = Field(
        description="List of most important features exposed to the front end for rendering"
    )
    prediction_interval: int = Field(
        description="Prediction interval for upper and lower bound of forecast"
    )

    use_case_id: str
    project_id: str
    model_id: str
    model_name: str
    date_format: str
    target: str = Field(
        description="Name of the untransformed target column in the training dataset"
    )
    multiseries_id_column: str
    feature_derivation_window_start: int
    feature_derivation_window_end: int
    forecast_window_start: int
    forecast_window_end: int
    timestep_settings: Dict[str, Any]
    datetime_partition_column: str = Field(
        description="Name of the untransformed datetime partition column in the training dataset"
    )
    datetime_partition_column_transformed: str = Field(
        description="Name of the DataRobot renamed datetime partition column"
    )
    training_dataset_id: str
    calendar_id: str
    filterable_categories: List[CategoryFilter] = Field(
        description="List of filterable categories"
    )
    page_description: str
    lower_bound_forecast_at_0: bool
    graph_y_axis: str
    page_title: str
    headline_prompt: str
    model_config = ConfigDict(protected_namespaces=())

    @classmethod
    def from_registered_model_version(
        cls,
        target: str,
        registered_model_id: str,
        registered_model_version_id: str,
        what_if_features: List[FeatureSettingConfig],
        important_features: List[dict[str, Any]],
        prediction_interval: int,
        static_app_settings: StaticAppSettings,
    ) -> AppSettings:
        registered_model_version = dr.RegisteredModel.get(  # type: ignore
            registered_model_id
        ).get_version(registered_model_version_id)
        if registered_model_version.source_meta.get("project_id", None) is None:
            raise ValueError(
                "Registered model version must be associated with a DR modeling project"
            )
        use_case_id = cast(
            str,
            registered_model_version.source_meta.get("use_case_details").get("id"),  # type: ignore
        )
        project_id = cast(str, registered_model_version.source_meta.get("project_id"))
        project = dr.Project.get(project_id)  # type: ignore
        datetime_partitioning = dr.DatetimePartitioning.get(project_id)
        datetime_partitioning_specification = datetime_partitioning.get_input_data(
            project_id, datetime_partitioning.datetime_partitioning_id
        )
        if (
            datetime_partitioning_specification.multiseries_id_columns is None
            or not len(datetime_partitioning_specification.multiseries_id_columns)
        ):
            raise ValueError(
                "Registered model mut be associated with a multiseries DR modeling project"
            )
        else:
            multiseries_id_column = (
                datetime_partitioning_specification.multiseries_id_columns[0]
            )
        training_dataset = project.get_dataset()
        if training_dataset is None:
            raise ValueError(
                "Registered model must be associated with a DR modeling project trained "
                "from an AI Catalog dataset"
            )
        else:
            training_dataset_id = training_dataset.id

        return AppSettings(
            registered_model_id=registered_model_id,
            registered_model_version_id=registered_model_version_id,
            what_if_features=what_if_features,
            important_features=important_features,
            prediction_interval=prediction_interval,
            use_case_id=use_case_id,
            project_id=project_id,
            model_id=registered_model_version.model_id,
            model_name=dr.Model.get(  # type: ignore
                project_id, registered_model_version.model_id
            ).model_type,
            date_format=datetime_partitioning.date_format,
            target=target,
            multiseries_id_column=multiseries_id_column,
            feature_derivation_window_start=datetime_partitioning.feature_derivation_window_start,
            feature_derivation_window_end=datetime_partitioning.feature_derivation_window_end,
            forecast_window_start=datetime_partitioning.forecast_window_start,
            forecast_window_end=datetime_partitioning.forecast_window_end,
            timestep_settings=cls.get_timestamp_settings(
                project_id,
                datetime_partitioning_specification.datetime_partition_column,
            ),
            datetime_partition_column=datetime_partitioning_specification.datetime_partition_column,
            datetime_partition_column_transformed=datetime_partitioning.datetime_partition_column,
            training_dataset_id=training_dataset_id,
            calendar_id=datetime_partitioning.calendar_id,
            filterable_categories=static_app_settings.filterable_categories,
            page_description=static_app_settings.page_description,
            lower_bound_forecast_at_0=static_app_settings.lower_bound_forecast_at_0,
            graph_y_axis=static_app_settings.graph_y_axis,
            page_title=static_app_settings.page_title,
            headline_prompt=static_app_settings.headline_prompt,
        )

    @classmethod
    def get_timestamp_settings(
        cls, project_id: str, datetime_partition_column_raw: str
    ) -> Dict[str, Any]:
        url = f"projects/{project_id}/features/{datetime_partition_column_raw}/multiseriesProperties"
        response = dr.Client().get(url).json()  # type: ignore
        timestep_settings: dict[str, Any] = response["detectedMultiseriesIdColumns"][0]
        del timestep_settings["multiseriesIdColumns"]
        return timestep_settings


class MultiSelectFilter(BaseModel):
    column_name: str
    display_name: str
    valid_values: List[str]


class FilterSpec(BaseModel):
    column: str
    selected_values: List[str]


class PredictionRow(BaseModel):
    date_id: str
    prediction: float
    low: float
    high: float


class ExplanationRow(BaseModel):
    feature_name: str
    relative_importance: float
    is_target_derived: bool


class ForecastSummary(BaseModel):
    headline: str
    summary_body: str
    feature_explanations: list[ExplanationRow]


class AppUrls(BaseModel):
    dataset: str
    model: str
    deployment: str
