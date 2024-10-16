# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from __future__ import annotations

from typing import Any, Tuple

import datarobot as dr
import pandas as pd
from datarobotx.idp.datasets import get_or_create_dataset_from_file

from .common.schema import DatasetArgs


def _test_parameter_names_are_valid(
    dataset: pd.DataFrame,
    target: str,
    datetime_partition_column: str,
    multiseries_id_columns: list[str],
    feature_settings_config: dict[str, Any],
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
                column["feature_name"] in feature_names  # type: ignore
                for column in feature_settings_config or []
            ]
        ), f"Feature settings columns {feature_settings_config['feature_settings']['featurelist']} not found in training dataset. {warning_text}"

    return True


def load_datasets(
    use_case_id: str,
    training_dataset_args: DatasetArgs,
    scoring_dataset_args: DatasetArgs,
) -> Tuple[str, str]:
    client = dr.client.get_client()
    token, endpoint = client.token, client.endpoint
    training_dataset = get_or_create_dataset_from_file(
        endpoint=endpoint,
        token=token,
        file_path=training_dataset_args.file_path,
        name=training_dataset_args.name,
        use_cases=use_case_id,
    )
    scoring_dataset = get_or_create_dataset_from_file(
        endpoint=endpoint,
        token=token,
        file_path=scoring_dataset_args.file_path,
        name=scoring_dataset_args.name,
        use_cases=use_case_id,
    )
    return training_dataset, scoring_dataset
