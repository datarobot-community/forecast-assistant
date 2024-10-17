# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from .common.schema import DatasetArgs
from .settings_main import project_name

training_dataset = DatasetArgs(
    resource_name=f"Forecast Assistant Training Data [{project_name}]",
    file_path="assets/store_sales_train.csv",
)
scoring_dataset = DatasetArgs(
    resource_name=f"Forecast Assistant Scoring Data [{project_name}]",
    file_path="assets/store_sales_predict.csv",
)
