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


from enum import Enum
from typing import List, Optional

from openai import BaseModel
from pydantic import Field


class CVMethod(str, Enum):
    RandomCV = "RandomCV"
    StratifiedCV = "StratifiedCV"


class Metric(str, Enum):
    Accuracy = "Accuracy"
    AUC = "AUC"
    BalancedAccuracy = "Balanced Accuracy"
    FVEBinomial = "FVE Binomial"
    GiniNorm = "Gini Norm"
    KolmogorovSmirnov = "Kolmogorov-Smirnov"
    LogLoss = "LogLoss"
    RateAtTop5 = "Rate@Top5%"
    RateAtTop10 = "Rate@Top10%"
    TPR = "TPR"
    FPR = "FPR"
    TNR = "TNR"
    PPV = "PPV"
    NPV = "NPV"
    F1 = "F1"
    MCC = "MCC"
    FVEGamma = "FVE Gamma"
    FVEPoisson = "FVE Poisson"
    FVETweedie = "FVE Tweedie"
    GammaDeviance = "Gamma Deviance"
    MAE = "MAE"
    MAPE = "MAPE"
    PoissonDeviance = "Poisson Deviance"
    RSquared = "R Squared"
    RMSE = "RMSE"
    RMSLE = "RMSLE"
    TweedieDeviance = "Tweedie Deviance"


class ValidationType(str, Enum):
    CV = "CV"
    TVH = "TVH"


# Enumerated Values¶
# Property 	Value
# type 	[schedule, data_drift_decline, accuracy_decline, None]
class TriggerType(str, Enum):
    schedule = "schedule"
    data_drift_decline = "data_drift_decline"
    accuracy_decline = "accuracy_decline"
    trigger_none = "None"


class Action(str, Enum):
    CreateChallenger = "create_challenger"
    CreateModelPackage = "create_model_package"
    ModelReplacement = "model_replacement"


class FeatureListStrategy(str, Enum):
    InformativeFeatures = "informative_features"
    SameAsChampion = "same_as_champion"


class ModelSelectionStrategy(str, Enum):
    AutopilotRecommended = "autopilot_recommended"
    SameBlueprint = "same_blueprint"
    SameHyperparameters = "same_hyperparameters"


class ProjectOptionsStrategy(str, Enum):
    SameAsChampion = "same_as_champion"
    OverrideChampion = "override_champion"
    Custom = "custom"


class AutopilotMode(str, Enum):
    auto = "auto"
    quick = "quick"
    comprehensive = "comprehensive"


class AutopilotOptions(BaseModel):
    blend_best_models: bool = True
    mode: AutopilotMode = AutopilotMode.quick
    run_leakage_removed_feature_list: bool = True
    scoring_code_only: bool = False
    shap_only_mode: bool = False


class Periodicity(BaseModel):
    time_steps: int = 0
    time_unit: str = "MILLISECOND"


class Schedule(BaseModel):
    day_of_months: List[str] = ["*"]
    day_of_weeks: List[str] = ["*"]
    hours: List[str] = ["*"]
    minutes: List[str] = ["*"]
    months: List[str] = ["*"]


class Trigger(BaseModel):
    min_interval_between_runs: Optional[str] = None
    schedule: Schedule = Field(default_factory=Schedule)
    status_declines_to_failing: bool = True
    status_declines_to_warning: bool = True
    status_still_in_decline: Optional[bool] = True
    type: TriggerType = TriggerType.schedule


class ProjectOptions(BaseModel):
    cv_method: CVMethod = CVMethod.RandomCV
    holdout_pct: Optional[float] = None
    metric: Metric = Metric.Accuracy
    reps: Optional[int] = None
    validation_pct: Optional[float] = None
    validation_type: ValidationType = ValidationType.CV


class TimeSeriesOptions(BaseModel):
    calendar_id: Optional[str] = None
    differencing_method: str = "auto"
    exponentially_weighted_moving_alpha: Optional[int] = None
    periodicities: Optional[List[Periodicity]] = None
    treat_as_exponential: Optional[str] = "auto"
