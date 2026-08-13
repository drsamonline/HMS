const DEFAULTS = Object.freeze({
  manualServerUrl: "",
  healthPath: "/api/v1/health/ready",
  discoveryProtocol: "hhms-lan-v1",
  discoveryRequest: "HHMS_DISCOVER_V1",
});

export function loadClientConfig() {
  const saved = window.localStorage.getItem("hhms.client.config");
  if (!saved) return { ...DEFAULTS };
  try {
    const parsed = JSON.parse(saved);
    return { ...DEFAULTS, ...parsed };
  } catch {
    return { ...DEFAULTS };
  }
}

export function saveClientConfig(config) {
  const normalized = { ...DEFAULTS, ...config };
  window.localStorage.setItem("hhms.client.config", JSON.stringify(normalized));
  return normalized;
}
