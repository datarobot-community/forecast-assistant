# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from __future__ import annotations

import json
import sys

from pydantic import ValidationError

sys.path.append("../")
from forecastic.schema import AppSettings, DynamicAppSettings
from forecastic.settings_app import static_app_settings

try:
    with open("dynamic_app_settings.json") as f:
        dynamic_app_settings = DynamicAppSettings.model_validate(json.load(f))
        app_settings = AppSettings(
            **dynamic_app_settings.model_dump(), **static_app_settings.model_dump()
        )
except ValidationError as e:
    print(e)
    raise ValueError(
        (
            "Unable to read App settings. If running locally, verify you have selected "
            "the correct stack and that it is active using `pulumi stack output`. "
            "If running in DataRobot, verify your runtime parameters have been set correctly."
        )
    ) from e
