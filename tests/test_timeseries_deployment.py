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
import sys
from pathlib import Path
from typing import Any

import datarobot as dr
import pandas as pd
import pytest

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@contextlib.contextmanager
def cd(new_dir: Path):
    """Changes the current working directory to the given path and restores the old directory on exit."""
    prev_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(prev_dir)


@pytest.fixture
def new_dir():
    with cd("frontend"):
        sys.path.append(".")
        yield


@pytest.fixture
def scoring_data(dr_client, new_dir):
    from forecastic.resources import ScoringDataset

    return (
        dr.Dataset.get(ScoringDataset().id).get_as_dataframe().to_dict(orient="records")
    )


def test_ts_prediction(scoring_data: list[dict[str, Any]]):
    from forecastic.api import get_predictions, get_standardized_predictions

    predictions = get_predictions(scoring_data)
    predictions_standardized = get_standardized_predictions(scoring_data)
    assert len(predictions) > 0
    assert len(predictions_standardized) > 0

    assert (
        len(pd.DataFrame([i.model_dump() for i in predictions_standardized]).columns)
        == 4
    )
