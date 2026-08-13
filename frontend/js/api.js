import { loadClientConfig, saveClientConfig } from "./config.js";

let serverBaseUrl = null;

export function setServerBaseUrl(url) {
  const normalized = normalizeBaseUrl(url);
  serverBaseUrl = normalized;
  saveClientConfig({ manualServerUrl: normalized });
  return normalized;
}

export function getServerBaseUrl() {
  return serverBaseUrl;
}

export async function checkServer(baseUrl = serverBaseUrl) {
  if (!baseUrl) throw new Error("HHMS server address is not configured.");
  const config = loadClientConfig();
  const response = await fetch(`${baseUrl}${config.healthPath}`, {
    method: "GET",
    headers: { "Accept": "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`HHMS server returned HTTP ${response.status}.`);
  }
  return await response.json();
}

function normalizeBaseUrl(value) {
  const url = new URL(value);
  url.pathname = url.pathname.replace(/\/$/, "");
  return url.toString().replace(/\/$/, "");
}
