# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

import datarobot as dr
from datarobotx.idp.autopilot import get_or_create_autopilot_run
from datarobotx.idp.calendars import get_or_create_calendar_dataset_from_country_code

from .common.schema import AutopilotRunArgs, CalendarArgs


def run_ts_autopilot(
    create_calendar_args: CalendarArgs,
    autopilotrun_args: AutopilotRunArgs,
    training_dataset_id: str,
    use_case_id: str,
) -> tuple[str, str, str]:
    client = dr.client.get_client()
    token = client.token
    endpoint = client.endpoint

    calendar_id = get_or_create_calendar_dataset_from_country_code(
        endpoint=endpoint, token=token, **create_calendar_args.model_dump()
    )

    project_id = get_or_create_autopilot_run(
        endpoint=endpoint,
        token=token,
        calendar_id=calendar_id,
        dataset_id=training_dataset_id,
        use_case=use_case_id,
        **autopilotrun_args.model_dump(),
    )

    recommended_model_id = dr.ModelRecommendation.get(project_id).model_id  # type: ignore[attr-defined,union-attr]

    return project_id, recommended_model_id, calendar_id
