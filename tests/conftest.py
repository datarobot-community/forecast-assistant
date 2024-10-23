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


# mypy: ignore-errors

import logging
import os
import subprocess
import uuid
from typing import Callable

import datarobot as dr
import pytest
from dotenv import dotenv_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption(
        "--pulumi_up",
        action="store_true",
        default=False,
        help="Run pulumi up before conducting test. Otherwise use existing stack.",
    )
    parser.addoption(
        "--always_delete_stack",
        action="store_true",
        default=False,
        help="Delete the stack even in case of failure (Only used in case `pulumi_up` is True)",
    )


def mode(request, pytestconfig):
    if pytestconfig.getoption("pulumi_up") is False:
        os.environ["PULUMI_STACK_CONTEXT"] = "TEST_MOCK_STACK"
    return request.param


@pytest.fixture(scope="session")
def stack_name(pytestconfig):
    if pytestconfig.getoption("pulumi_up"):
        short_uuid = str(uuid.uuid4())[:5]
        return f"test-stack-{short_uuid}"
    else:
        return subprocess.check_output(
            [
                "pulumi",
                "stack",
                "--show-name",
                "--non-interactive",
            ],
            text=True,
        ).strip()


@pytest.fixture(scope="session")
def session_env_vars():
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    env_vars = dotenv_values(env_file)
    os.environ.update(env_vars)


@pytest.fixture(scope="session")
def subprocess_runner():
    def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(command, check=False, text=True, capture_output=True)
        cmd = " ".join(command)
        if proc.returncode:
            msg = f"'{cmd}' exited {proc.returncode}"
            logger.warning(msg)
            msg = f"'{cmd}' STDOUT:\n{proc.stdout}"
            logger.warning(msg)
            msg = f"'{cmd}' STDERR:\n{proc.stderr}"
            logger.warning(msg)
            logger.info(proc)
        return proc

    return run_command


@pytest.fixture(scope="session")
def pulumi_up(
    stack_name,
    session_env_vars,
    pytestconfig,
    request: pytest.FixtureRequest,
    subprocess_runner: Callable[[list[str]], subprocess.CompletedProcess[str]],
):
    if pytestconfig.getoption("pulumi_up"):
        logger.info(f"Running {stack_name} with {session_env_vars}")
        subprocess_runner(["pulumi", "stack", "init", stack_name, "--non-interactive"])
        # ensure stack is deleted - stack init can fail if the name is the same as currently selected
        subprocess_runner(
            ["pulumi", "stack", "select", stack_name, "--non-interactive"]
        )
        proc = subprocess_runner(["pulumi", "up", "-y", "--non-interactive"])
        stack = subprocess.check_output(["pulumi", "stack", "output"], text=True)

        if proc.returncode:
            raise RuntimeError(f"`pulumi up` failed for {stack_name}")
        os.environ["PULUMI_STACK_CONTEXT"] = stack_name
        tests_failed_before_module = request.session.testsfailed
        # logger.info(f"Tests failed before: {tests_failed_before_module}")
        yield
        tests_failed_during_module = (
            request.session.testsfailed - tests_failed_before_module
        )
        logger.info(f"New tests failed: {tests_failed_during_module}")

        # if we say "always delete" this will delete
        # if we say "don't always delete, this will only delete if no failures occured"
        if (
            pytestconfig.getoption("always_delete_stack") is True
            or tests_failed_during_module == 0
        ):
            logger.info("Tearing down stack")
            subprocess_runner(["pulumi", "down", "-y", "--non-interactive"])
            subprocess_runner(
                ["pulumi", "stack", "rm", stack_name, "-y", "--non-interactive"]
            )
        else:
            logger.warning(
                f"There were errors. The stack {stack_name} will be preserved. Please check logs."
            )
    else:
        stack = subprocess.check_output(
            ["pulumi", "stack"],
            text=True,
        ).split("\n")[0]
        logger.info(stack)
        yield


@pytest.fixture
def dr_client(session_env_vars):
    return dr.Client()
