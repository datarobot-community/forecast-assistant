# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from typing import Any, Dict, List


def test_parameter_names_are_valid(
    endpoint: str,
    token: str,
    dataset_id: str,
    target: str,
    datetime_partition_column: str,
    multiseries_id_columns: List[str],
    feature_settings_config: Dict[str, Any],
) -> bool:
    """Ensure parameter names are in training dataset."""
    import datarobot as dr

    dr.Client(endpoint=endpoint, token=token)

    training_dataset = dr.Dataset.get(dataset_id)
    features = training_dataset.get_all_features()
    feature_names = [feature.name for feature in features]
    warning_text = (
        "Please check and adjust the settings in `parameters_deploy_forecast.yml`."
    )

    assert (
        target in feature_names
    ), f"Target {target} not found in dataset. {warning_text}"
    assert (
        datetime_partition_column in feature_names
    ), f"datetime_partition_column {datetime_partition_column} not found in dataset. {warning_text}"
    assert all(
        [column in feature_names for column in multiseries_id_columns]
    ), f"Multiseries id columns {multiseries_id_columns} not found in dataset. {warning_text}"
    if feature_settings_config is not None:
        assert all(
            [
                column["feature_name"] in feature_names
                for column in feature_settings_config or []
            ]
        ), f"Feature settings columns {feature_settings_config['feature_settings']['featurelist']} not found in dataset. {warning_text}"

    return True


def add_datasets_to_use_case(
    endpoint: str,
    token: str,
    use_case_id: str,
    training_dataset_id: str,
    scoring_dataset_id: str,
    **kwargs,
) -> None:
    """Add datasets to the use case."""

    import datarobot as dr

    dr.Client(endpoint=endpoint, token=token)
    use_case = dr.UseCase.get(use_case_id)
    try:
        use_case.add(dr.Dataset.get(training_dataset_id))
    except dr.errors.ClientError:
        pass
    try:
        use_case.add(dr.Dataset.get(scoring_dataset_id))
    except dr.errors.ClientError:
        pass
    return
