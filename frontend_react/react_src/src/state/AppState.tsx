import React, { useReducer, createContext, useMemo } from "react";
import { nanoid } from "nanoid";
import useScoringData from "~/data/useScoringData";
import useConfigs, {
  type AppSettings,
  type RuntimeAttributes,
} from "~/data/useConfigs";
import {
  assignColorsToFeatures,
  convertPythonDateFormatToJavaScript,
} from "~/helpers";

export type ScoringData = {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
};

export type PredictionExplanation = {
  label: string;
  feature: string;
  featureValue: number;
  strength: number;
  qualitativeStrength: string;
};

export type ForecastData = {
  prediction: number;
  timestamp: string;
  predictionIntervals: {
    "80": {
      low: number;
      high: number;
    };
  };
  predictionExplanations: PredictionExplanation[];
  seriesId: string;
};

export type Feature = {
  name: string;
  color: string;
};

export type FilterableCategory = {
  name: string;
  displayName: string;
  options: string[];
};

type Filters = {
  [key: string]: string[];
};

export type WhatIfScenarioFeature = {
  featureName: string;
  values: {
    date: string | Date;
    value: number | string;
  }[];
};

export type WhatIfScenario = {
  id: string;
  name: string;
  description: string;
  features: WhatIfScenarioFeature[];
  forecastData?: ForecastData[];
  isLoadingForecastData?: boolean;
};

type AppState = {
  appSettings: AppSettings;
  runtimeAttributes: RuntimeAttributes;
  configsLoading: boolean;
  scoringData: ScoringData[];
  scoringDataLoading: boolean;
  datasetColumns: string[];
  filters: Filters;
  filterOptions: { [key: string]: FilterableCategory };
  inputDateFormat: string;
  outputDateFormat: string;
  doesDateContainTime: boolean;
  importantFeaturesWithColors: Feature[];
  forecastData: ForecastData[];
  forecastSeriesIdsCount: number;
  forecastDataLoading: boolean;
  naturalLanguageSummary: string;
  naturalLanguageSummaryLoading: boolean;
  selectedFeatures: Feature[];
  confidenceIntervalEnabled: boolean;
  predictionExplanationsEnabled: boolean;
  whatIfScenarios: WhatIfScenario[];
  activeWhatIfScenarioId: string | null;
  toggleConfidenceInterval: () => void;
  togglePredictionExplanations: () => void;
  setFilters: (filters: Filters) => void;
  setForecastData: (data: ForecastData[], seriesIdsCount?: number) => void;
  setForecastDataLoading: (loading: boolean) => void;
  setNaturalLanguageSummary: (summary: string) => void;
  setNaturalLanguageSummaryLoading: (loading: boolean) => void;
  addPredictionFeature: (feature: Feature) => void;
  removePredictionFeature: (feature: Feature) => void;
  resetPredictionFeatures: () => void;
  addWhatIfScenario: () => void;
  removeWhatIfScenario: (id: string) => void;
  duplicateWhatIfScenario: (id: string) => void;
  updateWhatIfScenario: (scenario: WhatIfScenario) => void;
  setWhatIfScenarioForecastData: (
    id: string,
    forecastData: ForecastData[]
  ) => void;
  setWhatIfScenarioLoadingForecastData: (id: string, loading: boolean) => void;
  setActiveWhatIfScenarioId: (id: string | null) => void;
};

type Action =
  | { type: "TOGGLE_CONFIDENCE_INTERVAL" }
  | { type: "TOGGLE_PREDICTION_EXPLANATIONS" }
  | { type: "SET_FILTERS"; payload: Filters }
  | {
      type: "SET_FORECAST_DATA";
      payload: {
        data: ForecastData[];
        seriesIdsCount?: number;
      };
    }
  | { type: "SET_FORECAST_DATA_LOADING"; payload: boolean }
  | { type: "SET_NATURAL_LANGUAGE_SUMMARY"; payload: string }
  | { type: "SET_NATURAL_LANGUAGE_SUMMARY_LOADING"; payload: boolean }
  | { type: "SET_PREDICTION_FEATURES"; payload: Feature[] }
  | { type: "ADD_PREDICTION_FEATURE"; payload: Feature }
  | { type: "REMOVE_PREDICTION_FEATURE"; payload: Feature }
  | { type: "RESET_PREDICTION_FEATURES" }
  | { type: "ADD_WHAT_IF_SCENARIO" }
  | { type: "REMOVE_WHAT_IF_SCENARIO"; payload: string }
  | { type: "DUPLICATE_WHAT_IF_SCENARIO"; payload: string }
  | { type: "UPDATE_WHAT_IF_SCENARIO"; payload: WhatIfScenario }
  | {
      type: "SET_WHAT_IF_SCENARIO_FORECAST_DATA";
      payload: {
        id: string;
        forecastData: ForecastData[];
      };
    }
  | {
      type: "SET_WHAT_IF_SCENARIO_LOADING_FORECAST_DATA";
      payload: { id: string; loading: boolean };
    }
  | { type: "SET_ACTIVE_WHAT_IF_SCENARIO_ID"; payload: string | null };

const INITIAL_STATE: AppState = {
  appSettings: {} as AppSettings,
  runtimeAttributes: {} as RuntimeAttributes,
  configsLoading: false,
  scoringData: [],
  scoringDataLoading: false,
  datasetColumns: [],
  filters: {},
  filterOptions: {},
  inputDateFormat: "",
  outputDateFormat: "",
  doesDateContainTime: false,
  importantFeaturesWithColors: [],
  forecastData: [],
  forecastSeriesIdsCount: 0,
  forecastDataLoading: false,
  naturalLanguageSummary: "",
  naturalLanguageSummaryLoading: false,
  selectedFeatures: [],
  confidenceIntervalEnabled: false,
  predictionExplanationsEnabled: false,
  whatIfScenarios: [],
  activeWhatIfScenarioId: null,
  toggleConfidenceInterval: () => {},
  togglePredictionExplanations: () => {},
  setFilters: () => {},
  setForecastData: () => {},
  setForecastDataLoading: () => {},
  setNaturalLanguageSummary: () => {},
  setNaturalLanguageSummaryLoading: () => {},
  addPredictionFeature: () => {},
  removePredictionFeature: () => {},
  resetPredictionFeatures: () => {},
  addWhatIfScenario: () => {},
  removeWhatIfScenario: () => {},
  duplicateWhatIfScenario: () => {},
  updateWhatIfScenario: () => {},
  setWhatIfScenarioForecastData: () => {},
  setWhatIfScenarioLoadingForecastData: () => {},
  setActiveWhatIfScenarioId: () => {},
};

const reducer = (state: AppState, action: Action) => {
  switch (action.type) {
    case "TOGGLE_CONFIDENCE_INTERVAL":
      return {
        ...state,
        confidenceIntervalEnabled: !state.confidenceIntervalEnabled,
      };
    case "TOGGLE_PREDICTION_EXPLANATIONS":
      return {
        ...state,
        predictionExplanationsEnabled: !state.predictionExplanationsEnabled,
      };
    case "SET_FILTERS":
      return {
        ...state,
        filters: action.payload,
        forecastData: [],
        naturalLanguageSummary: "",
        naturalLanguageSummaryLoading: false,
      };
    case "SET_FORECAST_DATA":
      return {
        ...state,
        forecastData: action.payload.data,
        forecastSeriesIdsCount:
          action.payload.seriesIdsCount || state.forecastSeriesIdsCount,
      };
    case "SET_FORECAST_DATA_LOADING":
      return { ...state, forecastDataLoading: action.payload };
    case "SET_NATURAL_LANGUAGE_SUMMARY":
      return { ...state, naturalLanguageSummary: action.payload };
    case "SET_NATURAL_LANGUAGE_SUMMARY_LOADING":
      return { ...state, naturalLanguageSummaryLoading: action.payload };
    case "SET_PREDICTION_FEATURES":
      return {
        ...state,
        selectedFeatures: action.payload,
      };
    case "ADD_PREDICTION_FEATURE":
      return {
        ...state,
        selectedFeatures: [...state.selectedFeatures, action.payload],
      };
    case "REMOVE_PREDICTION_FEATURE":
      return {
        ...state,
        selectedFeatures: state.selectedFeatures.filter(
          (feature) => feature.name !== action.payload.name
        ),
      };
    case "RESET_PREDICTION_FEATURES":
      return {
        ...state,
        selectedFeatures: [],
      };
    case "ADD_WHAT_IF_SCENARIO": {
      const scenario = {
        id: nanoid(),
        name: `Scenario #${state.whatIfScenarios.length + 1}`,
        description: "A new scenario description.",
        features: [],
      };
      return {
        ...state,
        whatIfScenarios: [...state.whatIfScenarios, scenario],
      };
    }
    case "REMOVE_WHAT_IF_SCENARIO":
      return {
        ...state,
        whatIfScenarios: state.whatIfScenarios.filter(
          (scenario) => scenario.id !== action.payload
        ),
      };
    case "DUPLICATE_WHAT_IF_SCENARIO": {
      const scenario = state.whatIfScenarios.find(
        (scenario) => scenario.id === action.payload
      );
      if (!scenario) return state;
      return {
        ...state,
        whatIfScenarios: [
          ...state.whatIfScenarios,
          {
            ...scenario,
            id: nanoid(),
            name: `${scenario.name} (Copy)`,
            isLoadingForecastData: false,
          },
        ],
      };
    }
    case "UPDATE_WHAT_IF_SCENARIO":
      return {
        ...state,
        whatIfScenarios: state.whatIfScenarios.map((scenario) =>
          scenario.id === action.payload.id
            ? {
                ...action.payload,
              }
            : scenario
        ),
      };
    case "SET_WHAT_IF_SCENARIO_FORECAST_DATA": {
      const { id, forecastData } = action.payload;
      return {
        ...state,
        whatIfScenarios: state.whatIfScenarios.map((scenario) =>
          scenario.id === id
            ? {
                ...scenario,
                forecastData,
                isLoadingForecastData: false,
              }
            : scenario
        ),
      };
    }
    case "SET_WHAT_IF_SCENARIO_LOADING_FORECAST_DATA": {
      const { id, loading } = action.payload;
      return {
        ...state,
        whatIfScenarios: state.whatIfScenarios.map((scenario) =>
          scenario.id === id
            ? {
                ...scenario,
                isLoadingForecastData: loading,
              }
            : scenario
        ),
      };
    }
    case "SET_ACTIVE_WHAT_IF_SCENARIO_ID":
      return { ...state, activeWhatIfScenarioId: action.payload };
    default:
      return state;
  }
};

export const AppStateContext = createContext<AppState>({} as AppState);

export const AppStateProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);

  const {
    appSettings,
    runtimeAttributes,
    loading: configsLoading,
  } = useConfigs();
  const {
    date_format: dateFormat,
    filterable_categories,
    important_features,
    datetime_partition_column: dateColumn,
  } = appSettings;

  const { inputDateFormat, outputDateFormat, doesDateContainTime } =
    useMemo(() => {
      let inputDateFormat = "";
      let outputDateFormat = "";

      if (!dateFormat) {
        return {
          inputDateFormat,
          outputDateFormat,
          doesDateContainTime: false,
        };
      }

      // convert the date format to a JS date format
      const jsDateFormat = convertPythonDateFormatToJavaScript(dateFormat);

      // check if the date format contains time
      const doesDateContainTime = jsDateFormat.includes("HH");

      inputDateFormat = jsDateFormat.replaceAll("-", "/");
      outputDateFormat = jsDateFormat + "";

      return {
        inputDateFormat,
        outputDateFormat,
        doesDateContainTime,
      };
    }, [dateFormat]);

  const {
    data: scoringData,
    loading: scoringDataLoading,
    filterOptions,
    datasetColumns,
  } = useScoringData({
    filterableCategories: filterable_categories,
    filters: state.filters,
    dateColumn,
    inputDateFormat,
  });

  const importantFeaturesWithColors = useMemo<Feature[]>(() => {
    const featuresWithColors = assignColorsToFeatures(important_features || []);

    // set the first 5 features to be selected by default
    const initialSelectedFeatures = featuresWithColors.slice(0, 5);
    dispatch({
      type: "SET_PREDICTION_FEATURES",
      payload: initialSelectedFeatures,
    });

    return featuresWithColors;
  }, [important_features]);

  const toggleConfidenceInterval = () => {
    dispatch({ type: "TOGGLE_CONFIDENCE_INTERVAL" });
  };

  const togglePredictionExplanations = () => {
    dispatch({ type: "TOGGLE_PREDICTION_EXPLANATIONS" });
  };

  const setFilters = (filters: Filters) => {
    dispatch({ type: "SET_FILTERS", payload: filters });
  };

  const setForecastData = (data: ForecastData[], seriesIdsCount?: number) => {
    dispatch({ type: "SET_FORECAST_DATA", payload: { data, seriesIdsCount } });
  };

  const setForecastDataLoading = (loading: boolean) => {
    dispatch({ type: "SET_FORECAST_DATA_LOADING", payload: loading });
  };

  const setNaturalLanguageSummary = (summary: string) => {
    dispatch({ type: "SET_NATURAL_LANGUAGE_SUMMARY", payload: summary });
  };

  const setNaturalLanguageSummaryLoading = (loading: boolean) => {
    dispatch({
      type: "SET_NATURAL_LANGUAGE_SUMMARY_LOADING",
      payload: loading,
    });
  };

  const addPredictionFeature = (feature: Feature) => {
    dispatch({ type: "ADD_PREDICTION_FEATURE", payload: feature });
  };

  const removePredictionFeature = (feature: Feature) => {
    dispatch({ type: "REMOVE_PREDICTION_FEATURE", payload: feature });
  };

  const resetPredictionFeatures = () => {
    dispatch({ type: "RESET_PREDICTION_FEATURES" });
  };

  const addWhatIfScenario = () => {
    dispatch({ type: "ADD_WHAT_IF_SCENARIO" });
  };

  const removeWhatIfScenario = (id: string) => {
    dispatch({ type: "REMOVE_WHAT_IF_SCENARIO", payload: id });
  };

  const duplicateWhatIfScenario = (id: string) => {
    dispatch({ type: "DUPLICATE_WHAT_IF_SCENARIO", payload: id });
  };

  const updateWhatIfScenario = (scenario: WhatIfScenario) => {
    dispatch({ type: "UPDATE_WHAT_IF_SCENARIO", payload: scenario });
  };

  const setWhatIfScenarioForecastData = (
    id: string,
    forecastData: ForecastData[]
  ) => {
    dispatch({
      type: "SET_WHAT_IF_SCENARIO_FORECAST_DATA",
      payload: { id, forecastData },
    });
  };

  const setWhatIfScenarioLoadingForecastData = (
    id: string,
    loading: boolean
  ) => {
    dispatch({
      type: "SET_WHAT_IF_SCENARIO_LOADING_FORECAST_DATA",
      payload: { id, loading },
    });
  };

  const setActiveWhatIfScenarioId = (id: string | null) => {
    dispatch({ type: "SET_ACTIVE_WHAT_IF_SCENARIO_ID", payload: id });
  };

  return (
    <AppStateContext.Provider
      value={{
        ...state,
        appSettings,
        runtimeAttributes,
        configsLoading,
        scoringData: scoringData || [],
        scoringDataLoading,
        datasetColumns,
        filterOptions,
        inputDateFormat,
        outputDateFormat,
        doesDateContainTime,
        toggleConfidenceInterval,
        togglePredictionExplanations,
        setFilters,
        importantFeaturesWithColors,
        setForecastData,
        setForecastDataLoading,
        setNaturalLanguageSummary,
        setNaturalLanguageSummaryLoading,
        addPredictionFeature,
        removePredictionFeature,
        resetPredictionFeatures,
        addWhatIfScenario,
        removeWhatIfScenario,
        duplicateWhatIfScenario,
        updateWhatIfScenario,
        setWhatIfScenarioForecastData,
        setWhatIfScenarioLoadingForecastData,
        setActiveWhatIfScenarioId,
      }}
    >
      {children}
    </AppStateContext.Provider>
  );
};
