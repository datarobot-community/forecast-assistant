# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.
from __future__ import annotations

import json
import subprocess
from typing import Any, Dict, Mapping, Tuple, Type, Union

from pydantic import AliasChoices, Field
from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from pydantic_settings.sources import parse_env_vars


class PulumiSettingsSource(EnvSettingsSource):
    """Pulumi stack outputs as a pydantic settings source."""

    _PULUMI_OUTPUTS: Dict[str, str] = {}
    _PULUMI_CALLED: bool = False

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.read_pulumi_outputs()
        super().__init__(*args, **kwargs)

    def read_pulumi_outputs(self) -> None:
        try:
            raw_outputs = json.loads(
                subprocess.check_output(
                    ["pulumi", "stack", "output", "-j"],
                    text=True,
                    stderr=subprocess.STDOUT,
                ).strip()
            )
            self._PULUMI_OUTPUTS = {
                k: v if isinstance(v, str) else json.dumps(v)
                for k, v in raw_outputs.items()
            }
        except BaseException:
            self._PULUMI_OUTPUTS = {}

    def _load_env_vars(self) -> Mapping[str, Union[str, None]]:
        return parse_env_vars(
            self._PULUMI_OUTPUTS,
            self.case_sensitive,
            self.env_ignore_empty,
            self.env_parse_none_str,
        )


class DynamicSettings(BaseSettings):
    """Settings that come from pulumi stack outputs or DR runtime parameters"""

    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            PulumiSettingsSource(settings_cls),
            env_settings,
        )


time_series_deployment_env_name: str = "FORECAST_DEPLOYMENT_ID"
scoring_dataset_env_name: str = "FORECAST_SCORING_DATASET_ID"
app_env_name: str = "DATAROBOT_APPLICATION_ID"


class TimeSeriesDeployment(DynamicSettings):
    id: str = Field(
        validation_alias=AliasChoices(
            "MLOPS_RUNTIME_PARAM_" + time_series_deployment_env_name,
            time_series_deployment_env_name,
        )
    )


class ScoringDataset(DynamicSettings):
    id: str = Field(
        validation_alias=AliasChoices(
            "MLOPS_RUNTIME_PARAM_" + scoring_dataset_env_name,
            scoring_dataset_env_name,
        )
    )
