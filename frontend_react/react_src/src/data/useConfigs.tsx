import { useEffect, useState } from "react";
import getAppSettings from "~/api/getAppSettings";
import getRuntimeAttributes from "~/api/getRuntimeAttributes";

export type ConfigFilterableCategory = {
  column_name: string;
  display_name: string;
};

export enum TimeUnit {
  MILLISECOND = "MILLISECOND",
  SECOND = "SECOND",
  MINUTE = "MINUTE",
  HOUR = "HOUR",
  DAY = "DAY",
  WEEK = "WEEK",
  MONTH = "MONTH",
  QUARTER = "QUARTER",
  YEAR = "YEAR",
}

export type ImportantFeature = {
  featureName: string;
  impactNormalized: number;
};

export type AppSettings = {
  date_format: string;
  datetime_partition_column: string;
  deployment_id: string;
  endpoint: string;
  feature_derivation_window_end: number;
  feature_derivation_window_start: number;
  filterable_categories: ConfigFilterableCategory[];
  forecast_window_end: number;
  forecast_window_start: number;
  graph_y_axis: string;
  important_features: ImportantFeature[];
  lower_bound_forecast_at_0: boolean;
  model_id: string;
  model_name: string;
  multiseries_id_column: string[];
  page_title: string;
  page_description: string;
  prediction_interval: string;
  project_id: string;
  scoring_dataset_id: string;
  target: string;
  timestep_settings: {
    timeStep: 1;
    timeUnit: TimeUnit;
  };
  what_if_features:
    | {
        feature_name: string;
        known_in_advance?: boolean;
        values?: string[] | number[];
      }[]
    | null;
};

export type RuntimeAttributes = {
  app_urls: {
    dataset: string;
    deployment: string;
    model: string;
  };
  app_creator_email: string;
  app_latest_created_date: string;
};

const useConfigs = () => {
  const [appSettings, setAppSettings] = useState<AppSettings>(
    {} as AppSettings
  );
  const [runtimeAttributes, setRuntimeAttributes] = useState<RuntimeAttributes>(
    {} as RuntimeAttributes
  );
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const appSettingsData = await getAppSettings();
        const runtimeAttributesData = await getRuntimeAttributes();
        setAppSettings(appSettingsData);
        setRuntimeAttributes(runtimeAttributesData);
      } catch (error) {
        console.error("Error fetching configs", error);
      }
      setLoading(false);
    };

    fetchData();
  }, []);

  return {
    appSettings,
    runtimeAttributes,
    loading,
  };
};

export default useConfigs;
