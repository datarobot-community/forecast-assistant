# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from __future__ import annotations
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


def test_parameter_names_are_valid(
    dataset: pd.DataFrame,
    target: str,
    datetime_partition_column: str,
    multiseries_id_columns: List[str],
    feature_settings_config: Dict[str, Any],
) -> bool:
    """Ensure parameter names are in training dataset."""

    feature_names = dataset.columns
    warning_text = (
        "Please check and adjust the settings in `parameters_deploy_forecast.yml`."
    )

    assert (
        target in feature_names
    ), f"Target {target} not found in dataset. {warning_text}"
    assert (
        datetime_partition_column in feature_names
    ), f"datetime_partition_column {datetime_partition_column} not found in training dataset. {warning_text}"
    assert all(
        [column in feature_names for column in multiseries_id_columns]
    ), f"Multiseries id columns {multiseries_id_columns} not found in training dataset. {warning_text}"
    if feature_settings_config is not None:
        assert all(
            [
                column["feature_name"] in feature_names
                for column in feature_settings_config or []
            ]
        ), f"Feature settings columns {feature_settings_config['feature_settings']['featurelist']} not found in training dataset. {warning_text}"

    return True
