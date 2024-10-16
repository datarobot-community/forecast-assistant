# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from pathlib import Path

from .common.schema import ApplicationSourceArgs
from .settings_main import project_name

_application_path = Path("frontend/")

app_source_args = ApplicationSourceArgs(
    resource_name="forecastic-app-source",
    name=f"Forecastic App Source [{project_name}]",
).model_dump(mode="json", exclude_none=True)

minimum_feature_importance = 0.05
app_resource_name: str = "forecastic-app"
app_name: str = f"Forecastic Application [{project_name}]"
