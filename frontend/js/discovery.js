import { loadClientConfig } from "./config.js";

export async function discoverServer() {
  const config = loadClientConfig();

  if (config.manualServerUrl) {
    return normalizeServer(config.manualServerUrl);
  }

  const bridge = window.hhms?.discovery;
  if (bridge && typeof bridge.discover === "function") {
    const discovered = await bridge.discover();
    if (discovered?.baseUrl) return normalizeServer(discovered.baseUrl);
  }

  return null;
}

export function normalizeServer(value) {
  const url = new URL(value);
  url.pathname = url.pathname.replace(/\/$/, "");
  return url.toString().replace(/\/$/, "");
}
