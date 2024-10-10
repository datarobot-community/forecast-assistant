# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from kedro.framework.hooks import hook_impl
from kedro.io import DataCatalog

from typing import Dict, Any


class ExtraCredentialsHooks:
    """Include credentials in the catalog so they can be used by nodes."""

    @hook_impl
    def after_catalog_created(
        self,
        catalog: DataCatalog,
        conf_catalog: Dict[str, Any],
        conf_creds: Dict[str, Any],
        save_version: str,
        load_versions: Dict[str, str],
    ) -> None:
        import datarobot as dr
        import openai

        dr_creds = conf_creds["datarobot"]
        azure_creds = conf_creds["azure_openai_llm_credentials"]

        prediction_server_id = dr_creds["prediction_environment_id"]
        if not any(
            [prediction_server_id == server.id for server in dr.PredictionServer.list()]
        ):
            msg = (
                "The value for `prediction_environment_id` specified in credentials.yml: "
                f"'{prediction_server_id}' does not correspond to an available prediction server."
            )
            raise ValueError(msg)

        client = openai.AzureOpenAI(
            api_key=azure_creds["api_key"],
            azure_endpoint=azure_creds["azure_endpoint"],
            api_version=azure_creds["api_version"],
        )

        client.chat.completions.create(
            messages=[{"role": "user", "content": "hello"}],
            model=azure_creds["deployment_name"],
        )
