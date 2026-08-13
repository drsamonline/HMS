import{loadClientConfig,saveClientConfig}from"./config.js";let serverBaseUrl=null;
export function setServerBaseUrl(url){const normalized=normalizeBaseUrl(url);serverBaseUrl=normalized;saveClientConfig({manualServerUrl:normalized});return normalized}
export function getServerBaseUrl(){return serverBaseUrl}
export async function checkServer(baseUrl=serverBaseUrl){if(!baseUrl)throw new Error("HHMS server address is not configured.");const config=loadClientConfig();const r=await fetch(`${baseUrl}${config.healthPath}`,{headers:{Accept:"application/json"},cache:"no-store"});if(!r.ok)throw new Error(`HHMS server returned HTTP ${r.status}.`);return r.json()}
function normalizeBaseUrl(value){const u=new URL(value);if(!["http:","https:"].includes(u.protocol))throw new Error("HHMS server address must use HTTP or HTTPS.");u.pathname=u.pathname.replace(/\/$/,"");return u.toString().replace(/\/$/,"")}
