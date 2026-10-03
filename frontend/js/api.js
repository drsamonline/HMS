import{loadClientConfig,saveClientConfig}from"./config.js";
let serverBaseUrl=null;let accessToken=sessionStorage.getItem("hhms.access_token");
export function setServerBaseUrl(url){const normalized=normalizeBaseUrl(url);serverBaseUrl=normalized;saveClientConfig({manualServerUrl:normalized});return normalized}
export function getServerBaseUrl(){return serverBaseUrl}
export function getAccessToken(){return accessToken}
export function clearAccessToken(){accessToken=null;sessionStorage.removeItem("hhms.access_token")}
async function request(path,options={}){
 const rawResponse=options.rawResponse===true;
 const requestOptions={...options};
 delete requestOptions.rawResponse;
 delete requestOptions.timeoutMs;
 if(!serverBaseUrl)throw new Error("HHMS server address is not configured.");
 const headers=new Headers(options.headers||{});
 headers.set("Accept","application/json");
 if(accessToken)headers.set("Authorization",`Bearer ${accessToken}`);
 if(options.body&&!headers.has("Content-Type"))headers.set("Content-Type","application/json");
 const controller=new AbortController();
 const timeoutMs=options.timeoutMs??15000;
 const timeoutId=setTimeout(()=>controller.abort(),timeoutMs);
 try{
  const r=await fetch(`${serverBaseUrl}${path}`,{...requestOptions,headers,cache:"no-store",signal:controller.signal});
  clearTimeout(timeoutId);
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
  if(rawResponse) return r;
  return r.status===204?null:r.json();
 }catch(error){
  if(error?.name==="AbortError"){
   window.dispatchEvent(new CustomEvent("hhms:request-timeout",{detail:{path}}));
   throw new Error(`HHMS server request timed out: ${path}`);
  }
  if(error instanceof TypeError||/Failed to fetch|NetworkError|fetch/i.test(String(error?.message||""))){
   window.dispatchEvent(new CustomEvent("hhms:server-state",{detail:{online:false}}));
   throw new Error("HHMS server is unreachable. Check the LAN connection or server address and try again.");
  }
  throw error;
 }finally{
  clearTimeout(timeoutId);
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
export async function buildInvoicePrintEnvelope(payload){return request("/api/v1/reports/invoice-print-envelope",{method:"POST",body:JSON.stringify(payload)});}

export async function listVisits(patientId){const q=new URLSearchParams({patient_id:String(patientId),skip:"0",limit:"100"});return request(`/api/v1/visits?${q.toString()}`)}
export async function listAdmissions(patientId){const q=new URLSearchParams({patient_id:String(patientId),skip:"0",limit:"100"});return request(`/api/v1/admissions?${q.toString()}`)}

export function getCurrentUserId(){try{const raw=sessionStorage.getItem("hhms.current_user");if(!raw)return null;const u=JSON.parse(raw);return u?.id??u?.user_id??null}catch{return null}}

const CLINICAL_CONTEXT_KEY="hhms.clinical_context";
export function saveClinicalContext(ctx={}){try{localStorage.setItem(CLINICAL_CONTEXT_KEY,JSON.stringify({visit_id:ctx.visit_id??null,admission_id:ctx.admission_id??null}))}catch{}}
export function loadClinicalContext(){try{return JSON.parse(localStorage.getItem(CLINICAL_CONTEXT_KEY)||"{}")}catch{return{}}}

export async function listCaseRecords(patientId){const q=new URLSearchParams({patient_id:String(patientId),skip:"0",limit:"100"});return request(`/api/v1/case-records?${q.toString()}`)}
export async function getCaseRecord(id){return request(`/api/v1/case-records/${encodeURIComponent(id)}`)}
export async function createCaseRecord(payload){return request("/api/v1/case-records",{method:"POST",body:JSON.stringify(payload)})}
export async function updateCaseRecord(id,payload){return request(`/api/v1/case-records/${encodeURIComponent(id)}`,{method:"PATCH",body:JSON.stringify(payload)})}

export async function listDiagnoses(caseId){const q=new URLSearchParams({case_record_id:String(caseId),skip:"0",limit:"100"});return request(`/api/v1/diagnoses?${q.toString()}`)}
export async function createDiagnosis(payload){return request("/api/v1/diagnoses",{method:"POST",body:JSON.stringify(payload)})}
export async function updateDiagnosis(id,payload){return request(`/api/v1/diagnoses/${encodeURIComponent(id)}`,{method:"PATCH",body:JSON.stringify(payload)})}
export async function listFollowups(caseId){const q=new URLSearchParams({case_record_id:String(caseId),skip:"0",limit:"100"});return request(`/api/v1/followups?${q.toString()}`)}
export async function listDueFollowups(fromIso,toIso,options={}){const q=new URLSearchParams({due_from:fromIso,due_to:toIso,skip:String(options.skip??0),limit:String(options.limit??100)});return request(`/api/v1/followups?${q.toString()}`)}
export async function getDashboardDueFollowups(options={}){const q=new URLSearchParams();if(options.from)q.set("from_datetime",options.from);q.set("days_ahead",String(options.daysAhead??7));q.set("limit",String(options.limit??100));return request(`/api/v1/dashboard/due-followups?${q.toString()}`)}
export async function getDashboardOutstandingInvoices(options={}){const q=new URLSearchParams({limit:String(options.limit??100)});return request(`/api/v1/dashboard/outstanding-invoices?${q.toString()}`)}
export async function getDashboardBedOccupancy(options={}){const q=new URLSearchParams({limit:String(options.limit??200)});return request(`/api/v1/dashboard/bed-occupancy?${q.toString()}`)}
export async function getDashboardPendingInvestigations(options={}){const q=new URLSearchParams({limit:String(options.limit??100)});return request(`/api/v1/dashboard/pending-investigations?${q.toString()}`)}
export async function getDashboardReceivablesAging(options={}){const q=new URLSearchParams({limit:String(options.limit??200)});return request(`/api/v1/dashboard/receivables-aging?${q.toString()}`)}

export async function getDashboardInvoiceReceiptContinuity(options={}){const q=new URLSearchParams({limit:String(options.limit??200)});return request(`/api/v1/dashboard/invoice-receipt-continuity?${q.toString()}`)}
export async function getDashboardReceiptNumberingContinuity(options={}){const q=new URLSearchParams({limit:String(options.limit??2000)});return request(`/api/v1/dashboard/receipt-numbering-continuity?${q.toString()}`)}
export async function getDashboardInvoicePaymentReconciliation(options={}){const q=new URLSearchParams({limit:String(options.limit??200)});return request(`/api/v1/dashboard/invoice-payment-reconciliation?${q.toString()}`)}
export async function getDashboardCollectionSummaryByPatient(options={}){const q=new URLSearchParams({limit:String(options.limit??200)});return request(`/api/v1/dashboard/collection-summary-by-patient?${q.toString()}`)}
export async function buildCollectionSummaryPrintEnvelope(payload){return request("/api/v1/reports/collection-summary-print-envelope",{method:"POST",body:JSON.stringify(payload)});}
export async function buildReceivablesAgingPrintEnvelope(payload){return request("/api/v1/reports/receivables-aging-print-envelope",{method:"POST",body:JSON.stringify(payload)});}
export async function createFollowup(payload){return request("/api/v1/followups",{method:"POST",body:JSON.stringify(payload)})}
export async function searchICD11(q){return request(`/api/v1/icd11/search?q=${encodeURIComponent(q)}&limit=15`)}
export async function createPrescription(payload){return request("/api/v1/prescriptions",{method:"POST",body:JSON.stringify(payload)})}

export async function createMedicine(payload){return request("/api/v1/medicines",{method:"POST",body:JSON.stringify(payload)})}
export async function updateMedicine(id,payload){return request(`/api/v1/medicines/${encodeURIComponent(id)}`,{method:"PATCH",body:JSON.stringify(payload)})}
export async function listMedicineBatches(medicineId,options={}){const q=new URLSearchParams({skip:"0",limit:"200",active_only:String(options.activeOnly!==false)});return request(`/api/v1/medicine-batches/medicine/${encodeURIComponent(medicineId)}?${q.toString()}`)}
export async function createMedicineBatch(payload){return request("/api/v1/medicine-batches",{method:"POST",body:JSON.stringify(payload)})}
export async function updateMedicineBatch(id,payload){return request(`/api/v1/medicine-batches/${encodeURIComponent(id)}`,{method:"PATCH",body:JSON.stringify(payload)})}

export async function listIPDAssessments(admissionId){const q=new URLSearchParams({admission_id:String(admissionId),skip:"0",limit:"100"});return request(`/api/v1/ipd-assessments?${q.toString()}`)}
export async function createIPDAssessment(payload){return request("/api/v1/ipd-assessments",{method:"POST",body:JSON.stringify(payload)})}
export async function createDischarge(payload){return request("/api/v1/discharges",{method:"POST",body:JSON.stringify(payload)})}
export async function getDischargeByAdmission(admissionId){return request(`/api/v1/discharges/admission/${encodeURIComponent(admissionId)}`)}
export async function createBed(payload){return request("/api/v1/beds",{method:"POST",body:JSON.stringify(payload)})}
export async function updateBed(id,payload){return request(`/api/v1/beds/${encodeURIComponent(id)}`,{method:"PATCH",body:JSON.stringify(payload)})}


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
export async function listCasePrescriptions(caseRecordId){return request(`/api/v1/prescriptions/by-case/${encodeURIComponent(caseRecordId)}`)}
export async function getPrescription(prescriptionId){return request(`/api/v1/prescriptions/${encodeURIComponent(prescriptionId)}`)}

export async function listInventoryItems(search=""){const q=new URLSearchParams({skip:"0",limit:"100",active_only:"true"});if(search.trim())q.set("search",search.trim());return request(`/api/v1/inventory-items?${q.toString()}`)}
export async function createInventoryItem(payload){return request("/api/v1/inventory-items",{method:"POST",body:JSON.stringify(payload)})}
export async function updateInventoryItem(id,payload){return request(`/api/v1/inventory-items/${encodeURIComponent(id)}`,{method:"PATCH",body:JSON.stringify(payload)})}
export async function listStockTransactions(itemId){return request(`/api/v1/stock-transactions/item/${encodeURIComponent(itemId)}?skip=0&limit=100`)}
export async function createStockTransaction(payload){return request("/api/v1/stock-transactions",{method:"POST",body:JSON.stringify(payload)})}

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

export async function listAdminUsers(){return request("/api/v1/administration/users");}
export async function createAdminUser(payload){return request("/api/v1/administration/users",{method:"POST",body:JSON.stringify(payload)});}
export async function updateAdminUser(id,payload){return request(`/api/v1/administration/users/${encodeURIComponent(id)}`,{method:"PATCH",body:JSON.stringify(payload)});}
export async function listAdminRoles(){return request("/api/v1/administration/roles");}
export async function createAdminRole(payload){return request("/api/v1/administration/roles",{method:"POST",body:JSON.stringify(payload)});}
export async function updateAdminRole(id,payload){return request(`/api/v1/administration/roles/${encodeURIComponent(id)}`,{method:"PATCH",body:JSON.stringify(payload)});}
export async function listAdminPermissions(){return request("/api/v1/administration/permissions");}

export async function listDesignations(){return request("/api/v1/designations?skip=0&limit=200");}
export async function createDesignation(payload){return request("/api/v1/designations",{method:"POST",body:JSON.stringify(payload)});}
export async function updateDesignation(id,payload){return request(`/api/v1/designations/${encodeURIComponent(id)}`,{method:"PATCH",body:JSON.stringify(payload)});}

export async function getHospitalSettings(){return request('/settings/hospital');}
export async function updateHospitalSettings(data){return request('/settings/hospital',{method:'PUT',body:JSON.stringify(data)});}
export async function listSystemSettings(){return request('/settings/system');}
export async function upsertSystemSetting(key,data){return request(`/settings/system/${encodeURIComponent(key)}`,{method:'PUT',body:JSON.stringify(data)});}
export async function listNumberSequences(){return request('/settings/sequences');}
export async function updateNumberSequence(id,data){return request(`/settings/sequences/${id}`,{method:'PATCH',body:JSON.stringify(data)});}

export async function listInvoiceItems(invoiceId){return apiGet(`/billing/invoices/${invoiceId}/items`)}
export async function createInvoiceItem(invoiceId,payload){return apiPost(`/billing/invoices/${invoiceId}/items`,payload)}
export async function deleteInvoiceItem(itemId){return apiDelete(`/billing/invoice-items/${itemId}`)}


export async function listAuditLogs(params = {}) {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) { if (value !== undefined && value !== null && value !== "") qs.set(key, value); }
  return request(`/audit-logs${qs.toString() ? `?${qs}` : ""}`);
}

export async function listServiceActivities(patientId = null) {
  const qs = new URLSearchParams();
  if (patientId) qs.set("patient_id", patientId);
  return request(`/service-activities${qs.toString() ? `?${qs}` : ""}`);
}

export async function apiGet(path, options = {}) { return request(path, { method: "GET", ...options }); }
export async function apiPost(path, body, options = {}) { return request(path, { method: "POST", body: JSON.stringify(body), ...options }); }
export async function apiDelete(path) { return request(path, { method: "DELETE" }); }

export async function listSuppliers(){return request("/api/v1/procurement/suppliers")}
export async function createSupplier(payload){return request("/api/v1/procurement/suppliers",{method:"POST",body:JSON.stringify(payload)})}
export async function listPurchaseOrders(status=""){const q=new URLSearchParams({});if(status)q.set("status",status);const suffix=q.toString()?`?${q.toString()}`:"";return request(`/api/v1/procurement/purchase-orders${suffix}`)}
export async function createPurchaseOrder(payload){return request("/api/v1/procurement/purchase-orders",{method:"POST",body:JSON.stringify(payload)})}
export async function createGoodsReceipt(payload){return request("/api/v1/procurement/goods-receipts",{method:"POST",body:JSON.stringify(payload)})}

export async function renewCurrentYearCase(patientId, options={}){const q=new URLSearchParams(); if(options.visit_id)q.set("visit_id",options.visit_id); if(options.admission_id)q.set("admission_id",options.admission_id); const suffix=q.toString()?`?${q}`:""; return request(`/api/v1/case-records/patient/${encodeURIComponent(patientId)}/renew-current-year${suffix}`,{method:"POST"});}
export async function getSystemHealth(){return request("/api/v1/health/system");}
export async function runMaintenance(){return apiPost("/maintenance/run",{});}
export async function vacuumDatabase(){return apiPost("/maintenance/vacuum",{});}
export async function listArchives(){return request("/maintenance/archives");}
export async function createYearArchive(year){return apiPost(`/maintenance/archives/${encodeURIComponent(year)}`,{});}
export async function getArchiveRolloverPreview(){return request("/maintenance/archives/rollover/preview");}
export async function rolloverArchiveYear(year){return apiPost(`/maintenance/archives/rollover/${encodeURIComponent(year)}`,{});}
export async function getHistoricalArchiveVisits(year,patientId){return request(`/maintenance/archives/${encodeURIComponent(year)}/patients/${encodeURIComponent(patientId)}/visits`);}
export async function getHistoricalArchiveInvoices(year,patientId){return request(`/maintenance/archives/${encodeURIComponent(year)}/patients/${encodeURIComponent(patientId)}/invoices`);}
export async function getHistoricalArchivePayments(year,patientId){return request(`/maintenance/archives/${encodeURIComponent(year)}/patients/${encodeURIComponent(patientId)}/payments`);}
export async function getHistoricalArchiveDispenses(year,patientId){return request(`/maintenance/archives/${encodeURIComponent(year)}/patients/${encodeURIComponent(patientId)}/dispenses`);}
export async function getHistoricalArchivePrescriptions(year,patientId){return request(`/maintenance/archives/${encodeURIComponent(year)}/patients/${encodeURIComponent(patientId)}/prescriptions`);}
export async function getHistoricalArchivePrescriptionItems(year,patientId){return request(`/maintenance/archives/${encodeURIComponent(year)}/patients/${encodeURIComponent(patientId)}/prescription-items`);}
export async function getHistoricalArchiveInvestigations(year,patientId){return request(`/maintenance/archives/${encodeURIComponent(year)}/patients/${encodeURIComponent(patientId)}/investigations`);}
export async function getHistoricalArchiveAdmissions(year,patientId){return request(`/maintenance/archives/${encodeURIComponent(year)}/patients/${encodeURIComponent(patientId)}/admissions`);}
export async function getHistoricalArchiveDocuments(year,patientId){return request(`/maintenance/archives/${encodeURIComponent(year)}/patients/${encodeURIComponent(patientId)}/documents`);}
export async function getHistoricalPurchaseOrders(year){return request(`/maintenance/archives/${encodeURIComponent(year)}/purchase-orders`);}
export async function getHistoricalGoodsReceipts(year){return request(`/maintenance/archives/${encodeURIComponent(year)}/goods-receipts`);}
export async function getHistoricalStockTransactions(year){return request(`/maintenance/archives/${encodeURIComponent(year)}/stock-transactions`);}
export async function getHistoricalStockCards(year){return request(`/maintenance/archives/${encodeURIComponent(year)}/stock-cards`);}

export async function getOperationalYear(){return apiGet('/operational-year');}
export async function apiPut(path, body, options = {}) { return request(path, { method: "PUT", body: JSON.stringify(body), ...options }); }
export async function updateOperationalYear(payload){return apiPut('/operational-year',payload);}

export async function getPatientHistory(patientId, years = []) {
  const qs = new URLSearchParams();
  for (const year of years) qs.append("year", String(year));
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return request(`/api/v1/patients/${encodeURIComponent(patientId)}/history${suffix}`);
}

export async function getPatientHistoryArchives(patientId) {
  return request(`/api/v1/patients/${encodeURIComponent(patientId)}/history/archives`);
}

export async function getPatientHistoryYearEvents(patientId, year){return request(`/api/v1/patients/${encodeURIComponent(patientId)}/history/years/${encodeURIComponent(year)}/events`);}
