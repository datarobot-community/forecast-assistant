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


from .common.schema import DatasetArgs
from .settings_main import project_name

training_dataset = DatasetArgs(
    resource_name=f"Forecast Assistant Training Data [{project_name}]",
    file_path="assets/store_sales_train.csv",
)
scoring_dataset = DatasetArgs(
    resource_name=f"Forecast Assistant Scoring Data [{project_name}]",
    file_path="assets/store_sales_predict.csv",
)
