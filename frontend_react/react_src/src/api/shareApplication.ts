import apiClient from "./apiClient";

const shareApplication = async (emails: string[]) => {
  return await apiClient.patch<void>("/share", emails, {});
};

export default shareApplication;
