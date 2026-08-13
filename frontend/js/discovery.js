import{loadClientConfig}from"./config.js";
export async function discoverServer(){const bridge=window.hhms?.discovery;if(bridge&&typeof bridge.discover==="function"){const found=await bridge.discover();if(found?.baseUrl)return normalizeServer(found.baseUrl)}const manual=loadClientConfig().manualServerUrl;return manual?normalizeServer(manual):null}
export function normalizeServer(value){const u=new URL(value);if(!["http:","https:"].includes(u.protocol))throw new Error("HHMS server address must use HTTP or HTTPS.");u.pathname=u.pathname.replace(/\/$/,"");return u.toString().replace(/\/$/,"")}
