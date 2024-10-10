# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

import glob
import pathlib
import re
import shutil


def remove_dev_snippet(file: pathlib.Path):
    with open(file, "r") as f:
        content = f.read()

    p = r"# <=== Begin dev snippet ===>.*# <=== End dev snippet ===>"
    content = re.sub(p, "", content, flags=re.DOTALL)

    with open(file, "w") as f:
        f.write(content)


# Copy files and templatize key directories
shutil.copytree(
    "recipe-forecastic-reactic",
    "{{ cookiecutter.repo_name }}",
    ignore=shutil.ignore_patterns(
        "pyproject.toml", "datarobotx", "data", "*globals.yml"
    ),
    dirs_exist_ok=True,
)

shutil.move(
    "{{ cookiecutter.repo_name }}/src/recipe_forecastic_reactic",
    "{{ cookiecutter.repo_name }}/src/{{ cookiecutter.python_package }}",
)

# Templatize configuration files
for filename in glob.iglob("{{ cookiecutter.repo_name }}/conf/**/**", recursive=True):
    file = pathlib.Path(filename)
    if file.is_file():
        file.write_text(
            file.read_text()
            .replace("${globals:project_name}", "{{ cookiecutter.project_name }}")
            .replace("recipe_forecastic_reactic", "{{ cookiecutter.python_package }}")
            .replace("_${globals:frontend}", "")
        )

shutil.copyfile("README.md", "{{ cookiecutter.repo_name }}/README.md")
shutil.copyfile("LICENSE.txt", "{{ cookiecutter.repo_name }}/LICENSE.txt")

# Delete drx assets if they exist in template
shutil.rmtree("{{ cookiecutter.repo_name }}/src/datarobotx", ignore_errors=True)

shutil.move(
    "{{ cookiecutter.repo_name }}/conf/local/example-credentials.yml",
    "{{ cookiecutter.repo_name }}/conf/local/credentials.yml",
)

package_path = pathlib.Path(
    "{{ cookiecutter.repo_name }}/src/{{ cookiecutter.python_package }}"
)
# Remove dev code blocks from settings.py and pipeline_registry.py
remove_dev_snippet(package_path / "settings.py")
remove_dev_snippet(package_path / "pipeline_registry.py")
