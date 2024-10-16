# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from __future__ import annotations

import sys

import pandas as pd
import streamlit as st
from local_helpers import (
    app_settings,
    create_chart,
    get_scoring_data,
    get_tldr,
    interpretChartHeadline,
    scoreForecast,
)

SCORING_DATASET_ID = app_settings.scoring_dataset_id
TARGET = app_settings.target
MULTISERIES_ID_COLUMN = app_settings.multiseries_id_column
CHART_CONFIG = {"displayModeBar": False, "responsive": True}

LOGO = "./DataRobot.png"

sys.setrecursionlimit(10000)

# Set the maximum number of rows and columns to be displayed
pd.set_option("display.max_rows", None)  # Display all rows
pd.set_option("display.max_columns", None)  # Display all columns

# Configure the page title, favicon, layout, etc
st.set_page_config(
    page_title=app_settings.page_title,
    layout="wide",
    page_icon="./datarobot_favicon.png",
)

with open("./style.css") as f:
    css = f.read()

st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def fpa() -> None:
    # Layout
    titleContainer = st.container()
    headlineContainer = st.container()
    chartContainer = st.container()
    explanationContainer = st.container()
    # Header
    with titleContainer:
        (
            col1,
            _,
        ) = titleContainer.columns([1, 2])
        col1.image(LOGO, width=200)
        st.markdown(
            f"<h1 style='text-align: center;'>{app_settings.page_title}</h1>",
            unsafe_allow_html=True,
        )

    df = get_scoring_data(SCORING_DATASET_ID)

    with st.sidebar:
        series_selection = df[MULTISERIES_ID_COLUMN].unique().tolist()

        with st.form(key="sidebar_form"):
            series = st.selectbox(MULTISERIES_ID_COLUMN, options=series_selection)
            n_records_to_display = st.number_input(
                "Number of records to display",
                min_value=10,
                max_value=200,
                value=90,
                step=10,
            )
            sidebarSubmit = st.form_submit_button(label="Run Forecast")
    if sidebarSubmit:
        if series is not None:
            with st.spinner("Processing forecast..."):
                scoring_data = (
                    df.loc[df[MULTISERIES_ID_COLUMN] == series]
                    .reset_index(drop=True)
                    .copy()
                )
                forecast_raw, forecast = scoreForecast(
                    scoring_data,
                )
            with st.spinner("Generating chart..."):
                st.session_state["chart_headline"] = interpretChartHeadline(
                    forecast=forecast
                )
                st.session_state["chart"] = create_chart(
                    scoring_data.tail(n_records_to_display),
                    forecast,
                    "Forecast for " + str(series),
                )
            with st.spinner("Generating explanation..."):
                explanations, explain_df = get_tldr(
                    forecast_raw,
                    TARGET,
                    temperature=0.0,
                )
                st.session_state["forecast_interpretation"] = explanations
                st.session_state["explanations_df"] = explain_df

    if "chart_headline" in st.session_state:
        headlineContainer.subheader(st.session_state["chart_headline"])
    if "chart" in st.session_state:
        chartContainer.plotly_chart(
            st.session_state["chart"], config=CHART_CONFIG, use_container_width=True
        )
    if "forecast_interpretation" in st.session_state:
        with explanationContainer:
            st.write("**AI Generated Analysis:**")
            st.write(st.session_state["forecast_interpretation"])
            with st.expander("Raw Explanations", expanded=False):
                st.write(st.session_state["explanations_df"])


def _main() -> None:
    hide_streamlit_style = """
    <style>
    # MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    fpa()


if __name__ == "__main__":
    _main()
