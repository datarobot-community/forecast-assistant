# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

import os
import subprocess

import pulumi


def get_stack() -> str:
    """Retrieve the active pulumi stack

    Attempt to retrieve from the pulumi runtime
    If no stack selected, attempt to infer from an env var

    Allows subprocesses w/o access to the pulumi runtime to see the active stack even
    if `pulumi up -s` syntax is used with no selected stack.
    """
    try:
        stack = pulumi.get_stack()
        if stack != "stack":
            os.environ["PULUMI_STACK_CONTEXT"] = stack
            return stack
    except Exception:
        pass
    try:
        return os.environ["PULUMI_STACK_CONTEXT"]
    except KeyError:
        pass
    try:
        return subprocess.check_output(
            ["pulumi", "stack", "--show-name", "--non-interactive"],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except subprocess.CalledProcessError:
        pass
    raise ValueError(
        (
            "Unable to retrieve the currently active stack. "
            "Verify you have selected created and selected a stack with `pulumi stack`."
        )
    )
