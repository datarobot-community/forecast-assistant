import { ForecastData } from "~/state/AppState";
import apiClient from "./apiClient";

type ReturnData = {
  headline: string;
  summary_body: string;
  feature_explanations: string;
};

const makeLlmRequest = async (forecastData: ForecastData[]) => {
  const { data } = await apiClient.post<ReturnData>(
    "/llmSummary",
    forecastData
  );
  return data;
};

export default makeLlmRequest;
