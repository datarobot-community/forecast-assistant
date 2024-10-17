# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

import os
from urllib.parse import urlsplit


def get_deployment_url(deployment_id: str) -> str:
    """Translate deployment ID to GUI URL.

    Parameters
    ----------
    deployment_id : str
        DataRobot deployment id.
    endpoint: str
        DataRobot public API endpoint e.g. envir
    """
    parsed_dr_url = urlsplit(os.environ["DATAROBOT_ENDPOINT"])
    return f"{parsed_dr_url.scheme}://{parsed_dr_url.netloc}/console-nextgen/deployments/{deployment_id}/"
