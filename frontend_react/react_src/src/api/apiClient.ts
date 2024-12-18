import axios from "axios";

let backendUrl = "http://localhost:8000";

if (import.meta.env.MODE === "production") {
  // expected valid url https://app.datarobot.com/custom_applications/{appId}/fastapi
  const fullUrl = window.location.origin + window.location.pathname;
  const baseURL = fullUrl.split("/").splice(0, 5).join("/");
  backendUrl = `${baseURL}/fastapi`;
}

const apiClient = axios.create({
  baseURL: backendUrl,
  headers: {
    Accept: "application/json",
    "Content-type": "application/json",
  },
});

export default apiClient;
