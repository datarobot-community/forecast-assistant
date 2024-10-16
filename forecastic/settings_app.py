# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from __future__ import annotations

import textwrap

from forecastic.schema import CategoryFilter, StaticAppSettings

static_app_settings = StaticAppSettings(
    filterable_categories=[
        CategoryFilter(column_name="Store", display_name="Store"),
        CategoryFilter(column_name="Region", display_name="Region"),
        CategoryFilter(column_name="Market", display_name="Market"),
    ],
    page_description="This application forecasts the sale revenue of a national retailer. The forecast can be focused by region, market, or store.",
    lower_bound_forecast_at_0=True,
    graph_y_axis="Sales ($)",
    page_title="Multistore Sales Forecast Interpreter",
    headline_prompt=textwrap.dedent("""\
        You are a data analyst and your job is to explain to non-technical executive business leaders what the data suggests.
        Executive leadership will provide a sales forecast and you will interpret it and summarize the outlook, highlighting key insights.
        Your response should be only 1 sentence long, not very wordy. It should be like a news headline. Do not put quotation marks around it.
        Your response, while insightful, should speak to the general direction of the forecast.
        Even if you're unsure, speak with confidence and certainty."""),
)
