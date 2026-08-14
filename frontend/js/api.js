import{loadClientConfig,saveClientConfig}from"./config.js";
let serverBaseUrl=null;let accessToken=sessionStorage.getItem("hhms.access_token");
export function setServerBaseUrl(url){const normalized=normalizeBaseUrl(url);serverBaseUrl=normalized;saveClientConfig({manualServerUrl:normalized});return normalized}
export function getServerBaseUrl(){return serverBaseUrl}
export function getAccessToken(){return accessToken}
export function clearAccessToken(){accessToken=null;sessionStorage.removeItem("hhms.access_token")}
async function request(path,options={}){
 if(!serverBaseUrl)throw new Error("HHMS server address is not configured.");
 const headers=new Headers(options.headers||{});
 headers.set("Accept","application/json");
 if(accessToken)headers.set("Authorization",`Bearer ${accessToken}`);
 if(options.body&&!headers.has("Content-Type"))headers.set("Content-Type","application/json");
 try{
  const r=await fetch(`${serverBaseUrl}${path}`,{...options,headers,cache:"no-store"});
  if(r.status===401){
   clearAccessToken();
   window.dispatchEvent(new CustomEvent("hhms:auth-expired"));
   throw new Error("Your HHMS session has expired. Please sign in again.");
  }
  if(!r.ok){
   let detail="";
   try{const body=await r.json();detail=body?.detail||body?.message||""}catch{}
   throw new Error(detail||`HHMS server returned HTTP ${r.status}.`);
  }
  window.dispatchEvent(new CustomEvent("hhms:server-state",{detail:{online:true}}));
  return r.status===204?null:r.json();
 }catch(error){
  if(error instanceof TypeError||/Failed to fetch|NetworkError|fetch/i.test(String(error?.message||""))){
   window.dispatchEvent(new CustomEvent("hhms:server-state",{detail:{online:false}}));
   throw new Error("HHMS server is unreachable. Check the LAN connection or server address and try again.");
  }
  throw error;
 }
}
export async function checkServer(baseUrl=serverBaseUrl){if(baseUrl)serverBaseUrl=normalizeBaseUrl(baseUrl);const c=loadClientConfig();return request(c.healthPath)}
export async function login(username,password){const c=loadClientConfig();const result=await request(c.loginPath,{method:"POST",body:JSON.stringify({username,password})});if(!result?.access_token)throw new Error("HHMS server returned an invalid authentication response.");accessToken=result.access_token;sessionStorage.setItem("hhms.access_token",accessToken);return result}
export async function listPatients(search=""){const c=loadClientConfig();const q=new URLSearchParams({skip:"0",limit:"50"});if(search.trim())q.set("search",search.trim());return request(`${c.patientsPath}?${q.toString()}`)}
export async function getPatient(patientId){const c=loadClientConfig();return request(`${c.patientsPath}/${encodeURIComponent(patientId)}`)}
export async function createPatient(payload){const c=loadClientConfig();return request(c.patientsPath,{method:"POST",body:JSON.stringify(payload)})}
function normalizeBaseUrl(value){const u=new URL(value);if(!["http:","https:"].includes(u.protocol))throw new Error("HHMS server address must use HTTP or HTTPS.");u.pathname=u.pathname.replace(/\/$/,"");return u.toString().replace(/\/$/,"")}
export async function listInvestigations(patientId,status=""){const q=new URLSearchParams({skip:"0",limit:"100"});if(patientId)q.set("patient_id",String(patientId));if(status)q.set("investigation_status",status);return request(`/api/v1/investigations?${q.toString()}`)}
export async function createInvestigation(payload){return request("/api/v1/investigations",{method:"POST",body:JSON.stringify(payload)})}
export async function updateInvestigation(id,payload){return request(`/api/v1/investigations/${encodeURIComponent(id)}`,{method:"PUT",body:JSON.stringify(payload)})}
export async function cancelInvestigation(id){return request(`/api/v1/investigations/${encodeURIComponent(id)}`,{method:"DELETE"})}
export async function listInvestigationResults(investigationId,status=""){const q=new URLSearchParams({skip:"0",limit:"100"});if(investigationId)q.set("investigation_id",String(investigationId));if(status)q.set("report_status",status);return request(`/api/v1/investigation-results?${q.toString()}`)}
export async function getInvestigationResult(investigationId){return request(`/api/v1/investigation-results/investigation/${encodeURIComponent(investigationId)}`)}
export async function createInvestigationResult(payload){return request("/api/v1/investigation-results",{method:"POST",body:JSON.stringify(payload)})}
export async function updateInvestigationResult(id,payload){return request(`/api/v1/investigation-results/${encodeURIComponent(id)}`,{method:"PUT",body:JSON.stringify(payload)})}
export async function listDepartments(){return request("/api/v1/departments?active_only=true&skip=0&limit=200")}
export async function listDepartmentServices(departmentId){return request(`/api/v1/department-services?department_id=${encodeURIComponent(departmentId)}&skip=0&limit=200`)}

export async function listInvoices(patientId,paymentStatus=""){const q=new URLSearchParams({skip:"0",limit:"100",patient_id:String(patientId)});if(paymentStatus)q.set("payment_status",paymentStatus);return request(`/api/v1/billing/invoices?${q.toString()}`)}
export async function createInvoice(payload){return request("/api/v1/billing/invoices",{method:"POST",body:JSON.stringify(payload)})}
export async function listInvoicePayments(invoiceId){return request(`/api/v1/billing/invoices/${encodeURIComponent(invoiceId)}/payments?skip=0&limit=100`)}
export async function createPayment(payload){return request("/api/v1/billing/payments",{method:"POST",body:JSON.stringify(payload)})}
export async function listPatientFiles(patientId){return request(`/api/v1/patient-files?patient_id=${encodeURIComponent(patientId)}&skip=0&limit=100`)}
export async function createPatientFile(payload){return request("/api/v1/patient-files",{method:"POST",body:JSON.stringify(payload)})}
export async function listArchiveRecords(patientFileId){return request(`/api/v1/archive-records?patient_file_id=${encodeURIComponent(patientFileId)}&skip=0&limit=100`)}
export async function createArchiveRecord(payload){return request("/api/v1/archive-records",{method:"POST",body:JSON.stringify(payload)})}

export async function getHospitalStatistics(startDate,endDate,departmentId="",serviceId=""){
 const q=new URLSearchParams({start_date:startDate,end_date:endDate});
 if(departmentId)q.set("department_id",departmentId); if(serviceId)q.set("service_id",serviceId);
 return request(`/api/v1/statistics/hospital?${q.toString()}`);
}
export async function getReportCatalog(){return request("/api/v1/reports/catalog");}
export async function buildClinicalReport(payload){return request("/api/v1/reports/clinical-data",{method:"POST",body:JSON.stringify(payload)});}
export async function buildPrintManifest(payload){return request("/api/v1/reports/clinical-data/print-manifest",{method:"POST",body:JSON.stringify(payload)});}
export async function buildPrintEnvelope(payload){return request("/api/v1/reports/clinical-data/print-envelope",{method:"POST",body:JSON.stringify(payload)});}
export async function buildClinicalBatch(payload){return request("/api/v1/reports/clinical-data/batch",{method:"POST",body:JSON.stringify(payload)});}

export async function listVisits(patientId){const q=new URLSearchParams({patient_id:String(patientId),skip:"0",limit:"100"});return request(`/api/v1/visits?${q.toString()}`)}
export async function listAdmissions(patientId){const q=new URLSearchParams({patient_id:String(patientId),skip:"0",limit:"100"});return request(`/api/v1/admissions?${q.toString()}`)}


export async function createDepartment(payload){return request("/api/v1/departments",{method:"POST",body:JSON.stringify(payload)})}
export async function updateDepartment(id,payload){return request(`/api/v1/departments/${encodeURIComponent(id)}`,{method:"PATCH",body:JSON.stringify(payload)})}
export async function createDepartmentService(payload){return request("/api/v1/department-services",{method:"POST",body:JSON.stringify(payload)})}
export async function updateDepartmentService(id,payload){return request(`/api/v1/department-services/${encodeURIComponent(id)}`,{method:"PATCH",body:JSON.stringify(payload)})}

export async function getCurrentUserProfile(){return request("/api/v1/auth/me");}

export async function listMedicines(search=""){const q=new URLSearchParams({skip:"0",limit:"100",active_only:"true"});if(search.trim())q.set("search",search.trim());return request(`/api/v1/medicines?${q.toString()}`)}
export async function getMedicineStock(medicineId){return request(`/api/v1/stock-batches/medicine/${encodeURIComponent(medicineId)}?active_only=true&skip=0&limit=200`)}
export async function getDispensesForPrescriptionItem(itemId){return request(`/api/v1/dispenses/prescription-item/${encodeURIComponent(itemId)}`)}
export async function createDispense(payload){return request("/api/v1/dispenses",{method:"POST",body:JSON.stringify(payload)})}

export async function listPrescriptions(visitId){return request(`/api/v1/prescriptions?visit_id=${encodeURIComponent(visitId)}&skip=0&limit=100`)}
export async function getPrescription(prescriptionId){return request(`/api/v1/prescriptions/${encodeURIComponent(prescriptionId)}`)}

\nexport async function listInventoryItems(search=""){const q=new URLSearchParams({skip:"0",limit:"100",active_only:"true"});if(search.trim())q.set("search",search.trim());return request(`/api/v1/inventory-items?${q.toString()}`)}
export async function createInventoryItem(payload){return request("/api/v1/inventory-items",{method:"POST",body:JSON.stringify(payload)})}
export async function updateInventoryItem(id,payload){return request(`/api/v1/inventory-items/${encodeURIComponent(id)}`,{method:"PATCH",body:JSON.stringify(payload)})}
export async function listStockTransactions(itemId){return request(`/api/v1/stock-transactions/item/${encodeURIComponent(itemId)}?skip=0&limit=100`)}
export async function createStockTransaction(payload){return request("/api/v1/stock-transactions",{method:"POST",body:JSON.stringify(payload)})}

export async function listVisits(patientId){return request(`/api/v1/visits?patient_id=${encodeURIComponent(patientId)}&skip=0&limit=100`)}
export async function createVisit(payload){return request("/api/v1/visits",{method:"POST",body:JSON.stringify(payload)})}
export async function listOPDTokens(queueDate){return request(`/api/v1/opd-tokens?queue_date=${encodeURIComponent(queueDate)}&skip=0&limit=200`)}
export async function createOPDToken(payload){return request("/api/v1/opd-tokens",{method:"POST",body:JSON.stringify(payload)})}
export async function updateOPDToken(tokenId,payload){return request(`/api/v1/opd-tokens/${encodeURIComponent(tokenId)}`,{method:"PUT",body:JSON.stringify(payload)})}
export async function cancelOPDToken(tokenId){return request(`/api/v1/opd-tokens/${encodeURIComponent(tokenId)}`,{method:"DELETE"})}
export async function listBeds(filters={}){const q=new URLSearchParams({skip:"0",limit:"200",active_only:"true"});if(filters.ward)q.set("ward",filters.ward);if(filters.occupancy_status)q.set("occupancy_status",filters.occupancy_status);return request(`/api/v1/beds?${q.toString()}`)}
export async function createAdmission(payload){return request("/api/v1/admissions",{method:"POST",body:JSON.stringify(payload)})}
export async function updateAdmission(id,payload){return request(`/api/v1/admissions/${encodeURIComponent(id)}`,{method:"PATCH",body:JSON.stringify(payload)})}
export async function listAllAdmissions(status=""){const q=new URLSearchParams({skip:"0",limit:"100"});if(status)q.set("status",status);return request(`/api/v1/admissions?${q.toString()}`)}
export async function getBed(id){return request(`/api/v1/beds/${encodeURIComponent(id)}`)}

