import apiClient from "./apiClient";
import { type ScoringData } from "~/state/AppState";

type Filters = {
  [key: string]: string[];
};

const getScoringData = async (filters: Filters): Promise<ScoringData[]> => {
  const response = await apiClient.get<ScoringData[]>("/scoringData");
  return response.data;
};

export default getScoringData;
