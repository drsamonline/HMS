import{loadClientConfig,saveClientConfig}from"./config.js";
let serverBaseUrl=null;let accessToken=sessionStorage.getItem("hhms.access_token");
export function setServerBaseUrl(url){const normalized=normalizeBaseUrl(url);serverBaseUrl=normalized;saveClientConfig({manualServerUrl:normalized});return normalized}
export function getServerBaseUrl(){return serverBaseUrl}
export function getAccessToken(){return accessToken}
export function clearAccessToken(){accessToken=null;sessionStorage.removeItem("hhms.access_token")}
async function request(path,options={}){if(!serverBaseUrl)throw new Error("HHMS server address is not configured.");const headers=new Headers(options.headers||{});headers.set("Accept","application/json");if(accessToken)headers.set("Authorization",`Bearer ${accessToken}`);if(options.body&&!headers.has("Content-Type"))headers.set("Content-Type","application/json");const r=await fetch(`${serverBaseUrl}${path}`,{...options,headers,cache:"no-store"});if(r.status===401){clearAccessToken();throw new Error("Your HHMS session has expired. Please sign in again.")}if(!r.ok){let detail="";try{detail=(await r.json()).detail||""}catch{}throw new Error(detail||`HHMS server returned HTTP ${r.status}.`)}return r.status===204?null:r.json()}
export async function checkServer(baseUrl=serverBaseUrl){if(baseUrl)serverBaseUrl=normalizeBaseUrl(baseUrl);const c=loadClientConfig();return request(c.healthPath)}
export async function login(username,password){const c=loadClientConfig();const result=await request(c.loginPath,{method:"POST",body:JSON.stringify({username,password})});if(!result?.access_token)throw new Error("HHMS server returned an invalid authentication response.");accessToken=result.access_token;sessionStorage.setItem("hhms.access_token",accessToken);return result}
export async function listPatients(search=""){const c=loadClientConfig();const q=new URLSearchParams({skip:"0",limit:"50"});if(search.trim())q.set("search",search.trim());return request(`${c.patientsPath}?${q.toString()}`)}
export async function getPatient(patientId){const c=loadClientConfig();return request(`${c.patientsPath}/${encodeURIComponent(patientId)}`)}
export async function createPatient(payload){const c=loadClientConfig();return request(c.patientsPath,{method:"POST",body:JSON.stringify(payload)})}
function normalizeBaseUrl(value){const u=new URL(value);if(!["http:","https:"].includes(u.protocol))throw new Error("HHMS server address must use HTTP or HTTPS.");u.pathname=u.pathname.replace(/\/$/,"");return u.toString().replace(/\/$/,"")}
export async function listCaseRecords(patientId){const c=loadClientConfig();return request(`/api/v1/case-records?patient_id=${encodeURIComponent(patientId)}`)}
export async function createCaseRecord(payload){return request("/api/v1/case-records",{method:"POST",body:JSON.stringify(payload)})}
export async function updateCaseRecord(id,payload){return request(`/api/v1/case-records/${encodeURIComponent(id)}`,{method:"PATCH",body:JSON.stringify(payload)})}
export async function listDiagnoses(caseId){return request(`/api/v1/diagnoses?case_record_id=${encodeURIComponent(caseId)}`)}
export async function createDiagnosis(payload){return request("/api/v1/diagnoses",{method:"POST",body:JSON.stringify(payload)})}
export async function updateDiagnosis(id,payload){return request(`/api/v1/diagnoses/${encodeURIComponent(id)}`,{method:"PATCH",body:JSON.stringify(payload)})}
export async function searchICD11(q){return request(`/api/v1/icd11/search?q=${encodeURIComponent(q)}`)}
export async function listFollowups(caseId){return request(`/api/v1/followups?case_record_id=${encodeURIComponent(caseId)}`)}
export async function createFollowup(payload){return request("/api/v1/followups",{method:"POST",body:JSON.stringify(payload)})}
export async function createPrescription(payload){return request("/api/v1/prescriptions",{method:"POST",body:JSON.stringify(payload)})}
export async function getPrescription(id){return request(`/api/v1/prescriptions/${encodeURIComponent(id)}`)}
export async function listMedicines(search=""){const q=new URLSearchParams({active_only:"true",skip:"0",limit:"100"});if(search.trim())q.set("search",search.trim());return request(`/api/v1/medicines?${q.toString()}`)}
