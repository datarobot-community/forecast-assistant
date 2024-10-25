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


# mypy: ignore-errors

import logging
import subprocess

import pytest

logger = logging.getLogger(__name__)


def get_custom_app_id(app_resource_name):
    custom_app_url = subprocess.check_output(
        [
            "pulumi",
            "stack",
            "output",
            app_resource_name,
            "--non-interactive",
        ],
        text=True,
    ).strip()
    return custom_app_url.split("/")[-2]


@pytest.fixture
def forecast_application_name():
    from infra.settings_app_infra import app_resource_name

    return app_resource_name


def test_app_running(pulumi_up, dr_client, forecast_application_name):
    custom_app_id = get_custom_app_id(forecast_application_name)
    msg = f"Custom application ID: {custom_app_id}"
    logger.info(msg)

    url = f"customApplications/{custom_app_id}/"
    app_response = dr_client.get(url, timeout=30)
    app_status = app_response.json()["status"]

    assert app_status in ["running", "paused"]
