import apiClient from "./apiClient";
import { type RuntimeAttributes } from "~/data/useConfigs";

const getRuntimeAttributes = async (): Promise<RuntimeAttributes> => {
  const response = await apiClient.get<RuntimeAttributes>("/runtimeAttributes");
  return response.data;
};

export default getRuntimeAttributes;
