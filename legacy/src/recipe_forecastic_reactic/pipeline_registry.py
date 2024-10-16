# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

"""Project pipelines."""

from typing import Dict

from kedro.framework.project import find_pipelines
from kedro.pipeline import Pipeline


def register_pipelines() -> Dict[str, Pipeline]:
    """Register the project's pipelines.

    Returns:
        A mapping from pipeline names to ``Pipeline`` objects.
    """

    pipelines = find_pipelines()

    extra_pipelines = ["delete_assets"]
    # <=== Begin dev snippet ===>

    from pathlib import Path  # noqa: E402

    from kedro.utils import _find_kedro_project  # noqa: E402
    import yaml  # noqa: E402

    project_root = _find_kedro_project(Path(".").resolve())

    with open(project_root / "conf/base/globals.yml") as f:
        global_params = yaml.safe_load(f)

    exclude_source_pipeline = (
        "load_datasets_from_ai_catalog"
        if global_params.get("source", "file") == "file"
        else "load_datasets_from_file"
    )
    extra_pipelines.append(exclude_source_pipeline)

    # <=== End dev snippet ===>
    # remove non default pipeline
    default_pipelines = {k: v for k, v in pipelines.items() if k not in extra_pipelines}

    pipelines["__default__"] = sum(default_pipelines.values())
    return pipelines
