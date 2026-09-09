import axios from "axios";
import { clearSession } from "../auth";

const client = axios.create({
  baseURL: "http://127.0.0.1:5000/api",
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// A JWT lasts 15 minutes. When it expires mid-session, the backend returns 401/422
// on every subsequent request — without this, pages just show a generic "failed to
// load" error instead of sending the user back to log in again.
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const url = error.config?.url || "";
    const isAuthEndpoint = url.includes("/auth/login") || url.includes("/auth/register");

    if ((status === 401 || status === 422) && !isAuthEndpoint) {
      clearSession();
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login?expired=1";
      }
    }
    return Promise.reject(error);
  }
);

export default client;
