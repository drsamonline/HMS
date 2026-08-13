import { discoverServer } from "./discovery.js";
import { checkServer, setServerBaseUrl } from "./api.js";

const statusEl = document.querySelector("#status");
const retryButton = document.querySelector("#retry");

function setStatus(message) {
  statusEl.textContent = message;
}

async function connect() {
  retryButton.disabled = true;
  setStatus("Searching for HHMS server…");
  try {
    const server = await discoverServer();
    if (!server) {
      setStatus("HHMS server not found. Configure the server address and retry.");
      return;
    }

    setServerBaseUrl(server);
    setStatus("Checking HHMS server…");
    const health = await checkServer(server);
    setStatus(`${health.service} ${health.version} is online.`);
  } catch (error) {
    setStatus(error instanceof Error ? error.message : "Unable to connect to HHMS server.");
  } finally {
    retryButton.disabled = false;
  }
}

retryButton.addEventListener("click", connect);
connect();
