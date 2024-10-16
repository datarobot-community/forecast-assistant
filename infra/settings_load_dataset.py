# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from .common.schema import DatasetArgs
from .settings_main import project_name

training_dataset = DatasetArgs(
    resource_name="dataset-training",
    file_path="assets/store_sales_train.csv",
    name=f"Forecastic Training Data [{project_name}]",
)
scoring_dataset = DatasetArgs(
    resource_name="dataset-scoring",
    file_path="assets/store_sales_predict.csv",
    name=f"Forecastic Scoring Data [{project_name}]",
)
