# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.


import os
import sys
from typing import Any

import datarobot as dr
import pandas as pd
from flask import Flask, Response, request, send_from_directory
from local_helpers import app_settings
from openai.types.chat.chat_completion import ChatCompletion
from werkzeug.middleware.proxy_fix import ProxyFix

sys.path.append("../")
from forecastic.predict import (
    azure_client,
    credentials,
    make_datarobot_predictions,
)

app = Flask(__name__, static_folder="build/")
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)  # type: ignore[method-assign]


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path: str) -> Response:
    assert app.static_folder is not None
    if path != "" and os.path.exists(app.static_folder + "/" + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")


@app.route("/api/predictions", methods=["POST"])
def proxy_dr() -> tuple[Any, int]:
    try:
        prediction_data = pd.DataFrame.from_records(request.json)
        predictions = make_datarobot_predictions(prediction_data)
        predictions_dict = predictions.to_dict(orient="records")
        converted_preds = []
        for old_prediction in predictions_dict:
            prediction = {}
            prediction["timestamp"] = pd.to_datetime(
                old_prediction.pop(app_settings.datetime_partition_column)
            ).strftime(app_settings.date_format)
            prediction["predictionIntervals"] = {
                "80": {
                    "low": old_prediction.pop("PREDICTION_80_PERCENTILE_LOW"),
                    "high": old_prediction.pop("PREDICTION_80_PERCENTILE_HIGH"),
                }
            }
            prediction["prediction"] = old_prediction.pop(
                f"{app_settings.target} (actual)_PREDICTION"
            )
            prediction["seriesId"] = old_prediction.pop(
                app_settings.multiseries_id_column
            )
            prediction["predictionExplanations"] = [
                {
                    "label": f"Explanation {n}",
                    "feature": old_prediction.pop(f"EXPLANATION_{n}_FEATURE_NAME"),
                    "featureValue": old_prediction.pop(f"EXPLANATION_{n}_ACTUAL_VALUE"),
                    "strength": old_prediction.pop(f"EXPLANATION_{n}_STRENGTH"),
                    "qualitativeStrength": old_prediction.pop(
                        f"EXPLANATION_{n}_QUALITATIVE_STRENGTH"
                    ),
                }
                for n in range(1, 4)
            ]
            converted_preds.append(prediction)
        return {"data": converted_preds}, 200
    except Exception as e:
        print(e)
        return str(e), 500


@app.route("/api/openai", methods=["POST"])
def proxy_openai() -> tuple[Any, int]:
    try:
        response: ChatCompletion = azure_client.chat.completions.create(  # type: ignore[arg-type]
            model=credentials.azure_deployment, **request.json
        )
        return response.model_dump(mode="json"), 200
    except Exception as e:
        print(e)
        return str(e), 500


@app.route("/api/frontendParams", methods=["GET"])
def frontend_params() -> Any:
    client = dr.client.get_client()
    application_name = app_settings.application_name.replace(" ", "%20")
    endpoint = client.endpoint
    token = client.token
    FRONT_END_CONFIGS = app_settings.model_dump(mode="json")
    try:
        client = dr.Client(endpoint=endpoint, token=token)  # type: ignore[attr-defined]
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
def scoring_data() -> pd.DataFrame:
    dataset_id = app_settings.scoring_dataset_id
    datetime_partition_column = app_settings.datetime_partition_column
    multiseries_id_column = app_settings.multiseries_id_column
    date_format = app_settings.date_format

    df = (
        dr.Dataset.get(dataset_id)  # type: ignore[attr-defined]
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
def share_access() -> tuple[str, int]:
    FRONT_END_CONFIGS = app_settings.model_dump(mode="json")

    application_name = FRONT_END_CONFIGS["application_name"].replace(" ", "%20")
    client = dr.client.get_client()
    try:
        url = f"customApplications/?name={application_name}"
        application_id = client.get(url).json()["data"][0]["id"]
        url = f"customApplications/{application_id}/sharedRoles"
        roles = [
            {"role": "CONSUMER", "shareRecipientType": "user", "username": email}
            for email in request.json  # type: ignore[union-attr]
        ]
        payload = {"operation": "updateRoles", "roles": roles}
        client.patch(url, json=payload)
        return "Success", 200
    except Exception as e:
        return str(e), 500
