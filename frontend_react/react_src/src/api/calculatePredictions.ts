import apiClient from "./apiClient";
import { formatDateString } from "~/helpers";
import { type ScoringData, type ForecastData } from "~/state/AppState";

export type CalculatePredictionsPayload = {
  scoringData: ScoringData[];
  dateColumn: string;
  inputDateFormat: string;
  outputDateFormat: string;
};

type ReturnData = {
  data: ForecastData[];
  forecastSeriesIdsCount: number;
};

const calculatePredictions = async ({
  scoringData,
  dateColumn,
  inputDateFormat,
  outputDateFormat,
}: CalculatePredictionsPayload): Promise<ReturnData> => {
  const formattedScoringData = [...scoringData].map((d) => {
    return {
      ...d,
      [dateColumn]: formatDateString(d[dateColumn], outputDateFormat),
    };
  });

  const { data } = await apiClient.post<ForecastData[]>(
    "/predictions",
    formattedScoringData
  );
  const seriesIds = new Set<string>();
  const formattedData = data.map((d) => {
    const timestamp = formatDateString(d.timestamp, inputDateFormat);
    seriesIds.add(d.seriesId);

    return {
      ...d,
      timestamp,
    };
  });

  return {
    data: formattedData,
    forecastSeriesIdsCount: seriesIds.size,
  };
};

export default calculatePredictions;
