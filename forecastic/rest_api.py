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


import sys
from typing import Any, List, Optional

from fastapi import FastAPI

sys.path.append("..")

from forecastic.api import (
    get_app_settings,
    get_filters,
    get_formatted_predictions,
    get_llm_summary,
    get_runtime_attributes,
    get_scoring_data,
    share_access,
)
from forecastic.schema import (
    AppRuntimeAttributes,
    AppSettings,
    FilterSpec,
    ForecastSummary,
    MultiSelectFilter,
)

app = FastAPI()


@app.get("/appSettings")
async def get_app_settings_endpoint() -> AppSettings:
    return get_app_settings()


@app.get("/runtimeAttributes")
async def get_runtime_attributes_endpoint() -> AppRuntimeAttributes:
    return get_runtime_attributes()


@app.get("/filters")
async def get_filters_endpoint() -> List[MultiSelectFilter]:
    return get_filters()


@app.get("/scoringData")
async def get_scoring_data_endpoint(
    filter_selection: Optional[List[FilterSpec]] = None,
) -> list[dict[str, Any]]:
    return get_scoring_data(filter_selection)


@app.post("/predictions")
async def get_predictions_endpoint(
    scoring_data: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return get_formatted_predictions(scoring_data)


@app.post("/llmSummary")
async def get_llm_summary_endpoint(
    predictions: List[dict[str, Any]],
) -> ForecastSummary:
    return get_llm_summary(predictions)


@app.patch("/share")
async def share_endpoint(emails: List[str]) -> tuple[str, int]:
    return share_access(emails)
