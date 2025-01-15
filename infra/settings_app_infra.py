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

import textwrap
from typing import List, Tuple

import datarobot as dr
import pulumi
import pulumi_datarobot as datarobot

from forecastic.i18n import LanguageCode, LocaleSettings
from infra.common.globals import GlobalRuntimeEnvironment
from infra.common.schema import ApplicationSourceArgs
from infra.settings_main import (
    PROJECT_ROOT,
    model_training_output_file,
    model_training_output_name,
    project_name,
)

application_path = PROJECT_ROOT / "frontend"

app_source_args = ApplicationSourceArgs(
    resource_name=f"Forecast Assistant App Source [{project_name}]",
    base_environment_id=GlobalRuntimeEnvironment.PYTHON_39_STREAMLIT.value.id,
).model_dump(mode="json", exclude_none=True)

app_resource_name: str = f"Forecast Assistant Application [{project_name}]"
application_locale = LocaleSettings().app_locale


def ensure_app_settings(app_id: str) -> None:
    try:
        dr.client.get_client().patch(
            f"customApplications/{app_id}/",
            json={"allowAutoStopping": True},
            timeout=60,
        )
    except Exception:
        pulumi.warn("Could not enable autostopping for the Application")


def _prep_metadata_yaml(
    runtime_parameter_values: List[
        datarobot.ApplicationSourceRuntimeParameterValueArgs
    ],
) -> None:
    from jinja2 import BaseLoader, Environment

    llm_runtime_parameter_specs = "\n".join(
        [
            textwrap.dedent(
                f"""\
            - fieldName: {param.key}
              type: {param.type}
        """
            )
            for param in runtime_parameter_values
        ]
    )
    with open(application_path / "metadata.yaml.jinja") as f:
        template = Environment(loader=BaseLoader()).from_string(f.read())
    (application_path / "metadata.yaml").write_text(
        template.render(
            additional_params=llm_runtime_parameter_specs,
        )
    )


def get_app_files(
    runtime_parameter_values: List[
        datarobot.ApplicationSourceRuntimeParameterValueArgs
    ],
) -> List[Tuple[str, str]]:
    _prep_metadata_yaml(runtime_parameter_values)

    forecastic_path = PROJECT_ROOT / "forecastic"

    source_files = [
        (str(f), str(f.relative_to(application_path)))
        for f in application_path.glob("**/*")
        if f.is_file()
        and f.name != "metadata.yaml.jinja"
        and "train_model_output" not in f.name
    ] + [
        (str(forecastic_path / "__init__.py"), "forecastic/__init__.py"),
        (str(forecastic_path / "schema.py"), "forecastic/schema.py"),
        (str(forecastic_path / "api.py"), "forecastic/api.py"),
        (str(forecastic_path / "resources.py"), "forecastic/resources.py"),
        (str(forecastic_path / "credentials.py"), "forecastic/credentials.py"),
        (str(forecastic_path / "i18n.py"), "forecastic/i18n.py"),
        (
            str(model_training_output_file),
            f"forecastic/{model_training_output_name}".replace(f".{project_name}", ""),
        ),
    ]

    if application_locale != LanguageCode.EN:
        source_files.append(
            (
                str(
                    forecastic_path
                    / "locale"
                    / application_locale
                    / "LC_MESSAGES"
                    / "base.mo"
                ),
                f"forecastic/locale/{application_locale}/LC_MESSAGES/base.mo",
            )
        )
    return source_files
