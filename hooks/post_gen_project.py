# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

import os
from pathlib import Path
import shutil
import stat
import subprocess


def remove_readonly(func, path, excinfo):
    """Handle windows permission error.

    https://stackoverflow.com/questions/1889597/deleting-read-only-directory-in-python/1889686#1889686
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


def move_and_delete(src: Path, dst: Path):
    # Move the contents of the source directory to the destination directory
    for item in os.listdir(src):
        s = src / item
        d = dst / item
        shutil.move(s, d)

    # Remove the empty source directory
    os.rmdir(src)


DATAROBOTX_IDP_VERSION = "{{ cookiecutter.datarobotx_idp_version }}"


print("Copying latest datarobotx-idp source into project..\n")

clone_directory = os.path.join(os.getcwd())
print(f"Cloning datarobotx-idp into {clone_directory}\n")

subprocess.run(
    [
        "git",
        "clone",
        "--branch",
        DATAROBOTX_IDP_VERSION,
        "https://github.com/datarobot-community/datarobotx-idp.git",
    ],
    check=True,
)


shutil.copytree("datarobotx-idp/src/datarobotx", "src/datarobotx")
shutil.rmtree("datarobotx-idp", onerror=remove_readonly)

pipelines_folder = Path("src/{{ cookiecutter.python_package }}/pipelines/")  # fmt: skip
conf_folder = Path("conf/base/")
include_folder = Path("include/")

input_data_type = "{{ cookiecutter.data_type }}"
input_frontend = "{{ cookiecutter.frontend }}"


if input_data_type == "ai_catalog":
    shutil.rmtree(
        pipelines_folder / "load_datasets_from_file",
        onerror=remove_readonly,
    )
    os.rename(
        pipelines_folder / "load_datasets_from_ai_catalog",
        pipelines_folder / "load_datasets",
    )
    shutil.rmtree(conf_folder / "file_datasource", onerror=remove_readonly)
    move_and_delete(conf_folder / "ai_catalog_datasource", conf_folder)

    shutil.rmtree(include_folder / "autopilot")


else:
    shutil.rmtree(
        pipelines_folder / "load_datasets_from_ai_catalog",
        onerror=remove_readonly,
    )
    os.rename(
        pipelines_folder / "load_datasets_from_file",
        pipelines_folder / "load_datasets",
    )
    shutil.rmtree(conf_folder / "ai_catalog_datasource", onerror=remove_readonly)
    move_and_delete(conf_folder / "file_datasource", conf_folder)

if input_frontend == "react":
    shutil.rmtree(include_folder / "app_streamlit", onerror=remove_readonly)
    os.rename(include_folder / "app_react", include_folder / "app")
else:
    shutil.rmtree(include_folder / "app_react", onerror=remove_readonly)
    os.rename(include_folder / "app_streamlit", include_folder / "app")

# Handle case when kedro new happens in a DataRobot codespace
if "DATAROBOT_DEFAULT_USE_CASE" in os.environ:
    import datarobot as dr
    import yaml

    parameters_yaml = Path("conf/base/parameters_load_datasets.yml")
    use_case = dr.UseCase.get(os.environ["DATAROBOT_DEFAULT_USE_CASE"])

    with open(parameters_yaml, "r") as file:
        parameters = yaml.safe_load(file)
        parameters["load_datasets"]["use_case"]["name"] = use_case.name
        parameters["load_datasets"]["use_case"]["description"] = use_case.description
    with open(parameters_yaml, "w") as file:
        yaml.dump(parameters, file)
