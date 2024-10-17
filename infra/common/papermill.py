# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

import pathlib
import sys
from typing import Optional

import papermill as pm


def run_notebook(
    nb_path: pathlib.Path, output_path: Optional[pathlib.Path] = None
) -> None:
    pm.execute_notebook(
        nb_path,
        output_path,
        cwd=nb_path.parent,
        log_output=False,
        progress_bar=False,
        stderr_file=sys.stderr,
        stdout_file=sys.stdout,
    )
