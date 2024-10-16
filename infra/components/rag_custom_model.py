# Copyright 2024 DataRobot, Inc. and its affiliates.
# All rights reserved.
# DataRobot, Inc.
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
# Released under the terms of DataRobot Tool and Utility Agreement.

from typing import List, Optional

import pulumi
import pulumi_datarobot as datarobot

from ..common.schema import (
    CustomModelArgs,
    DatasetArgs,
    LLMBlueprintArgs,
    PlaygroundArgs,
    VectorDatabaseArgs,
)


class RAGCustomModel(pulumi.ComponentResource):
    def __init__(
        self,
        resource_name: str,
        use_case: datarobot.UseCase,
        dataset_args: DatasetArgs,
        playground_args: PlaygroundArgs,
        vector_database_args: VectorDatabaseArgs,
        llm_blueprint_args: LLMBlueprintArgs,
        runtime_parameter_values: List[datarobot.CustomModelRuntimeParameterValueArgs],
        guard_configurations: List[datarobot.CustomModelGuardConfigurationArgs],
        custom_model_args: CustomModelArgs,
        opts: Optional[pulumi.ResourceOptions] = None,
    ):
        super().__init__("custom:datarobot:RAGCustomModel", resource_name, None, opts)

        self.playground = datarobot.Playground(
            use_case_id=use_case.id,
            **playground_args.model_dump(mode="json"),
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.vdb_dataset = datarobot.DatasetFromFile(
            use_case_ids=[use_case.id],
            **dataset_args.model_dump(mode="json"),
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.vector_database = datarobot.VectorDatabase(
            dataset_id=self.vdb_dataset.id,
            use_case_id=use_case.id,
            **vector_database_args.model_dump(mode="json"),
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.llm_blueprint = datarobot.LlmBlueprint(
            playground_id=self.playground.id,
            vector_database_id=self.vector_database.id,
            **llm_blueprint_args.model_dump(mode="json"),
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.custom_model = datarobot.CustomModel(
            source_llm_blueprint_id=self.llm_blueprint.id,
            runtime_parameter_values=runtime_parameter_values,
            guard_configurations=guard_configurations,
            **custom_model_args.model_dump(mode="json", exclude_none=True),
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs(
            {
                "playground_id": self.playground.id,
                "dataset_id": self.vdb_dataset.id,
                "vector_database_id": self.vector_database.id,
                "llm_blueprint_id": self.llm_blueprint.id,
                "id": self.custom_model.id,
                "version_id": self.custom_model.version_id,
            }
        )

    @property
    @pulumi.getter(name="versionId")
    def version_id(self) -> pulumi.Output[str]:
        """
        The ID of the latest Custom Model version.
        """
        return pulumi.get(self.custom_model, "version_id")  # type: ignore[no-any-return]
