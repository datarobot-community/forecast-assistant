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


import contextlib
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import pytest
from streamlit.testing.v1 import AppTest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@contextlib.contextmanager
def cd(new_dir: Path) -> Any:
    """Changes the current working directory to the given path and restores the old directory on exit."""
    prev_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(prev_dir)


@pytest.fixture
def application(
    pulumi_up: Any,
    subprocess_runner: Callable[[list[str]], subprocess.CompletedProcess[str]],
) -> Any:
    stack_name = subprocess.check_output(
        ["pulumi", "stack", "--show-name"],
        text=True,
    ).split("\n")[0]
    with cd("frontend"):  # type: ignore[arg-type]
        subprocess_runner(
            ["pulumi", "stack", "select", stack_name, "--non-interactive"]
        )
        # and ensure we can access `frontend` as if we were running from inside
        sys.path.append(".")
        logger.info(subprocess.check_output(["pulumi", "stack", "output"]))
        yield AppTest.from_file("app.py", default_timeout=30)


@pytest.fixture
def app_post_forecast(application: AppTest) -> AppTest:
    at = application.run()
    at.multiselect("filter_Store").set_value(["Portland", "Baltimore"])
    at.multiselect("filter_Market").set_value(["Corporate"])
    at.button[0].click().run(timeout=60)
    return at


def test_produces_a_forecast(app_post_forecast: AppTest) -> None:
    assert len(app_post_forecast.session_state.forecast_processed) > 0
    assert app_post_forecast.session_state.chart_json is not None


def test_produces_a_summary(app_post_forecast: AppTest) -> None:
    headline = app_post_forecast.session_state.headline
    summary = app_post_forecast.session_state.forecast_interpretation
    assert headline in app_post_forecast.markdown[3].value
    assert summary in app_post_forecast.markdown[4].value
