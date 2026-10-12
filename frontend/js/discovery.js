import{loadClientConfig}from"./config.js";
// When the GUI is served by HHMS itself (http://<server>:8000/), the origin IS the server: connect with zero prompts, no UDP needed. This also survives DHCP IP changes because the browser bookmark always resolves to the current address.
export function sameOriginServer(){try{if(typeof location!=="undefined"&&["http:","https:"].includes(location.protocol))return normalizeServer(location.origin)}catch{return null}return null}
// In the WebView2 desktop client the page runs from a virtual host, so the
// origin is not the server; the native C# bridge performs real LAN discovery.
function hasNativeBridge(){try{return!!(window.hhms&&typeof window.hhms.discovery?.discover==="function")}catch{return false}}
// Browser fallback for "local machine" auto-discovery when there is no UDP
// bridge and the page was NOT served by HHMS (e.g. opened from disk or a dev
// static server): probe the conventional localhost port directly over HTTP.
// A failed fetch rejects instantly on loopback, so this costs milliseconds.
async function probeLocalServer(){const port=loadClientConfig().defaultServerPort||8000;for(const host of["127.0.0.1","localhost"]){const base=`http://${host}:${port}/api/v1`;try{const r=await fetch(`${base}${loadClientConfig().healthPath}`,{signal:AbortSignal.timeout(1200)});if(r.ok)return normalizeServer(base)}catch{}}return null}
export async function discoverServer(){const manual=loadClientConfig().manualServerUrl;if(manual)return normalizeServer(manual);if(hasNativeBridge()){try{const found=await window.hhms.discovery.discover();if(found?.baseUrl){const base=normalizeServer(found.baseUrl);if(sameOriginServer()===base)return base;const probe=await fetch(`${base}${loadClientConfig().healthPath}`,{signal:AbortSignal.timeout(1500)}).catch(()=>null);if(probe?.ok)return base}}catch{}}else{const local=await probeLocalServer();if(local)return local}return sameOriginServer()}
export function normalizeServer(value){const u=new URL(value);if(!["http:","https:"].includes(u.protocol))throw new Error("HHMS server address must use HTTP or HTTPS.");u.pathname=u.pathname.replace(/\/$/,"");return u.toString().replace(/\/$/,"")}
