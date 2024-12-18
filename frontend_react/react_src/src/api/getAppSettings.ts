import apiClient from "./apiClient";
import { type AppSettings } from "~/data/useConfigs";

const getAppSettings = async (): Promise<AppSettings> => {
  const response = await apiClient.get<AppSettings>("/appSettings");
  return response.data;
};

export default getAppSettings;
