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

import json
import os
from typing import Any, Dict, Optional

import requests


def get_application_source_resources(source_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch application source resources from DataRobot API.

    Args:
        source_id: The ID of the application source

    Returns:
        Dictionary containing the resources configuration, or None if not found

    Raises:
        RuntimeError: If API call fails or required environment variables are missing
    """
    # Get DataRobot endpoint and token from environment
    endpoint = os.getenv("DATAROBOT_ENDPOINT")
    token = os.getenv("DATAROBOT_API_TOKEN")

    if not endpoint:
        raise RuntimeError("DATAROBOT_ENDPOINT environment variable is required")

    if not token:
        raise RuntimeError("DATAROBOT_API_TOKEN environment variable is required")

    # Construct API URL - handle case where endpoint might already include api/v2
    base_endpoint = endpoint.rstrip("/")
    if "/api/v2" in base_endpoint:
        api_url = f"{base_endpoint}/customApplicationSources/{source_id}/"
    else:
        api_url = f"{base_endpoint}/api/v2/customApplicationSources/{source_id}/"

    # Make API request
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()

        data = response.json()

        # Extract resources from latest version
        latest_version = data.get("latestVersion", {})
        resources = latest_version.get("resources")

        return resources if resources is not None else None

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch application source resources: {e}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse API response: {e}")
