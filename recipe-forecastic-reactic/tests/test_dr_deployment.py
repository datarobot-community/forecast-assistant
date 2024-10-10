# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.


import datarobot as dr
import pandas as pd
import pytest


@pytest.fixture
def model_input(project_context, dr_client):
    multiseries_id_column = project_context.config_loader["parameters"][
        "deploy_forecast"
    ]["project"]["datetime_partitioning_config"]["multiseries_id_columns"][0]
    scoring_dataset = project_context.catalog.load("scoring_dataset_id")
    data = dr.Dataset.get(scoring_dataset).get_as_dataframe()
    series_id = data.at[0, multiseries_id_column]
    return data.loc[data[multiseries_id_column] == series_id].to_json(orient="records")


def test_forecast_deployment_prediction(project_context, make_prediction, model_input):
    deployment_id = project_context.catalog.load("deployment_id")
    output = pd.DataFrame(make_prediction(model_input, deployment_id)["data"])
    assert isinstance(output, pd.DataFrame)
    assert len(output) > 0
