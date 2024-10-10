# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.


import os
from urllib.parse import urljoin

import datarobot as dr
from flask import Flask, send_from_directory, request
import pandas as pd
import requests
from werkzeug.middleware.proxy_fix import ProxyFix

from local_helpers import construct_credentials

CREDENTIALS, FRONT_END_CONFIGS = construct_credentials("../..")

app = Flask(__name__, static_folder="build/")
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path != "" and os.path.exists(app.static_folder + "/" + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")


@app.route("/api/predictions", methods=["POST"])
def proxy_dr():
    dr_credentials = CREDENTIALS["datarobot"]
    prediction_server = FRONT_END_CONFIGS["prediction_server"]
    try:
        url = prediction_server["prediction_request_url"]
        dr_api_token = dr_credentials["api_token"]
        dr_key = prediction_server["datarobot_key"]
        headers = request.headers
        headers = {
            "Authorization": f"Bearer {dr_api_token}",
            "DataRobot-Key": dr_key,
            **dict(request.headers),
        }

        response = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.data,
            params=request.args,
        )
        return response.json(), response.status_code
    except Exception as e:
        return str(e), 500


@app.route("/api/openai", methods=["POST"])
def proxy_openai():
    openai_credentials = CREDENTIALS["openai"]
    try:
        openai_endpoint = openai_credentials["endpoint"]
        openai_api_key = openai_credentials["api_key"]
        openai_version = openai_credentials["api_version"]
        deployment = openai_credentials["deployment"]
        route = f"/openai/deployments/{deployment}/chat/completions?api-version={openai_version}"
        url = urljoin(openai_endpoint, route)
        headers = request.headers
        headers = {"api-key": openai_api_key}

        response = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.data,
            params=request.args,
        )
        return response.json(), response.status_code
    except Exception as e:
        return str(e), 500


@app.route("/api/frontendParams", methods=["GET"])
def frontend_params():
    application_name = FRONT_END_CONFIGS["application_name"].replace(" ", "%20")
    endpoint = FRONT_END_CONFIGS["endpoint"]
    token = CREDENTIALS["datarobot"]["api_token"]
    try:
        client = dr.Client(endpoint=endpoint, token=token)
        url = f"customApplications/?name={application_name}"
        application_details = client.get(url).json()["data"][0]
        FRONT_END_CONFIGS["created_at"] = application_details["createdAt"]
        FRONT_END_CONFIGS["created_by"] = application_details["createdBy"]
    except IndexError:
        FRONT_END_CONFIGS["created_at"] = None
        FRONT_END_CONFIGS["created_by"] = "Local"
    except Exception as e:
        return str(e), 500

    return FRONT_END_CONFIGS


@app.route("/api/scoringData", methods=["GET"])
def scoring_data():
    endpoint = FRONT_END_CONFIGS["endpoint"]
    token = CREDENTIALS["datarobot"]["api_token"]
    dr.Client(endpoint=endpoint, token=token)

    dataset_id = FRONT_END_CONFIGS["scoring_dataset_id"]
    datetime_partition_column = FRONT_END_CONFIGS["datetime_partition_column"]
    multiseries_id_column = FRONT_END_CONFIGS["multiseries_id_column"][0]
    date_format = FRONT_END_CONFIGS["date_format"]

    df = (
        dr.Dataset.get(dataset_id)
        .get_as_dataframe()
        .assign(
            date_sort_column=lambda x: pd.to_datetime(
                x[datetime_partition_column], format=date_format
            )
        )
        .sort_values(by=[multiseries_id_column, "date_sort_column"])
        .reset_index(drop=True)
    )
    return df.to_json(orient="records")


@app.route("/api/share", methods=["PATCH"])
def share_access():
    endpoint = FRONT_END_CONFIGS["endpoint"]
    token = CREDENTIALS["datarobot"]["api_token"]
    client = dr.Client(endpoint=endpoint, token=token)

    application_name = FRONT_END_CONFIGS["application_name"].replace(" ", "%20")

    try:
        url = f"customApplications/?name={application_name}"
        application_id = client.get(url).json()["data"][0]["id"]
        url = f"customApplications/{application_id}/sharedRoles"
        roles = [
            {"role": "CONSUMER", "shareRecipientType": "user", "username": email}
            for email in request.json
        ]
        payload = {"operation": "updateRoles", "roles": roles}
        client.patch(url, json=payload)
        return "Success", 200
    except Exception as e:
        return str(e), 500
