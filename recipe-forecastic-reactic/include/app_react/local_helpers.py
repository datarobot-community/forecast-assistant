# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from __future__ import annotations
import json
import os
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from kedro.io import DataCatalog


def _get_kedro_catalog(kedro_project_root: str) -> DataCatalog:
    """Initialize a kedro data catalog (as a singleton)."""
    try:
        import pathlib
        from kedro.framework.startup import bootstrap_project
        from kedro.framework.session import KedroSession
    except ImportError as e:
        raise ImportError(
            "Please ensure you've installed `kedro` and `kedro_datasets` to run this app locally"
        ) from e

    project_path = pathlib.Path(kedro_project_root).resolve()
    bootstrap_project(project_path)
    session = KedroSession.create(project_path)
    context = session.load_context()

    return context.catalog


def construct_credentials(project_path: str) -> tuple:
    """Load credentials from the catalog."""

    credentials = {"datarobot": {}, "openai": {}}
    try:
        with open("frontend_config.yaml", "r") as f:
            front_end_configs = yaml.safe_load(f)
        credentials["datarobot"]["api_token"] = os.environ["DATAROBOT_API_TOKEN"]
        credentials["openai"]["endpoint"] = os.environ[
            "MLOPS_RUNTIME_PARAM_llm_endpoint"
        ]

        llm_api_key = os.environ["MLOPS_RUNTIME_PARAM_llm_api_key"]
        credentials["openai"]["api_key"] = json.loads(llm_api_key)["payload"][
            "apiToken"
        ]
        credentials["openai"]["api_version"] = os.environ[
            "MLOPS_RUNTIME_PARAM_llm_api_version"
        ]
        credentials["openai"]["deployment"] = os.environ[
            "MLOPS_RUNTIME_PARAM_llm_deployment_name"
        ]

    except FileNotFoundError:
        catalog = _get_kedro_catalog(project_path)
        dr_credentials = catalog.load("params:credentials.datarobot")
        front_end_config_path = catalog.load("deploy_application.frontend_config")
        with open(front_end_config_path, "r") as f:
            front_end_configs = yaml.safe_load(f)
        openai_credentials = catalog.load(
            "params:credentials.azure_openai_llm_credentials"
        )

        credentials["datarobot"]["api_token"] = dr_credentials["api_token"]
        credentials["openai"]["endpoint"] = openai_credentials["azure_endpoint"]
        credentials["openai"]["api_key"] = openai_credentials["api_key"]
        credentials["openai"]["api_version"] = openai_credentials["api_version"]
        credentials["openai"]["deployment"] = openai_credentials["deployment_name"]

    return credentials, front_end_configs
