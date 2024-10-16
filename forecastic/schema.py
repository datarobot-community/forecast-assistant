# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict


class FeatureSettingConfig(BaseModel):
    feature_name: str
    known_in_advance: bool | None = None
    do_not_derive: bool | None = None


class CategoryFilter(BaseModel):
    column_name: str
    display_name: str


class DynamicAppSettings(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    application_name: str
    project_id: str
    model_id: str
    model_name: str
    scoring_dataset_id: str
    date_format: str
    target: str
    multiseries_id_column: str
    feature_derivation_window_start: int
    feature_derivation_window_end: int
    forecast_window_start: int
    forecast_window_end: int
    what_if_features: List[FeatureSettingConfig]
    prediction_interval: float
    important_features: List[dict[str, Any]]
    timestep_settings: Dict[str, Any]
    app_urls: dict[str, Any]
    datetime_partition_column: str


class StaticAppSettings(BaseModel):
    page_title: str
    page_description: str
    graph_y_axis: str
    lower_bound_forecast_at_0: bool
    filterable_categories: List[CategoryFilter]
    headline_prompt: str


class AppSettings(StaticAppSettings, DynamicAppSettings):
    pass
