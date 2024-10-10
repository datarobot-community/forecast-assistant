# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

import traceback
from typing import Literal


def _write_exception_message(asset_id: str, asset_type: str):
    print(
        f"Unable to delete the {asset_type} associated with {asset_id}; "
        "check that the asset(s) weren't previously deleted."
    )
    print(traceback.format_exc())


def delete_assets(
    endpoint: str,
    token: str,
    use_case_id: str,
    deployment_id: str,
    application_id: str,
    dataset_type: Literal["from_file", "from_ai_catalog"],
):
    """Delete assets created by the pipeline."""
    import datarobot as dr

    client = dr.Client(endpoint=endpoint, token=token)

    try:
        app_url = f"customApplications/{application_id}/"
        custom_app_json = client.get(app_url).json()
        client.delete(app_url)
        client.delete(
            f"customApplicationSources/{custom_app_json['customApplicationSourceId']}/"
        )
    except Exception:
        _write_exception_message(application_id, "application")
        pass

    try:
        deployment = dr.Deployment.get(deployment_id)
        deployment.delete()
    except Exception:
        _write_exception_message(deployment_id, "deployment")

    try:
        registered_model = dr.RegisteredModel.get(
            deployment.model_package["registered_model_id"]
        )
        dr.RegisteredModel.archive(registered_model.id)
    except Exception:
        _write_exception_message(deployment_id, "registered model")

    try:
        project = dr.Project.get(deployment.model.get("project_id"))
        project.delete()
    except Exception:
        _write_exception_message(project.id, "project")

    if dataset_type == "from_file":
        try:
            dr.Dataset.delete(project.catalog_id)
        except Exception:
            _write_exception_message(project.catalog_id, "dataset")
    try:
        dr.UseCase.delete(use_case_id)
    except Exception:
        _write_exception_message(use_case_id, "use case")
