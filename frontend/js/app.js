import{discoverServer}from"./discovery.js";import{checkServer,setServerBaseUrl,getServerBaseUrl,login,listPatients,getPatient,createPatient,getAccessToken,clearAccessToken,getCurrentUserProfile}from"./api.js";import{clearSavedServer,loadClientConfig}from"./config.js";
import{openClinicalWorkspace}from"./clinical.js";
import{openIPDWorkspace}from"./ipd.js";
import{openInvestigationsWorkspace}from"./investigations.js";import{openBillingWorkspace}from"./billing.js";import{openMRDWorkspace}from"./mrd.js";import{openStatisticsWorkspace}from"./statistics.js";import{openReportsWorkspace}from"./reports.js";import{openDashboard}from"./dashboard.js";import{openPatientTimeline}from"./timeline.js";import{applyNavigationAccess,applyRecordAccess,canAccess}from"./rbac.js";
import{openAdministrationWorkspace}from"./admin.js";import{openInventoryWorkspace}from"./inventory.js";import{openProcurementWorkspace}from"./procurement.js";import{openActivityWorkspace}from"./activity.js";import{openPharmacyWorkspace}from"./pharmacy.js";
import{openSettingsWorkspace}from"./settings.js";
import{openHistoricalWorkspace}from"./historical.js";import{openBackupWorkspace}from"./backups.js";import{openOPDQueueWorkspace}from"./opd.js";
const $=s=>document.querySelector(s), state=$("#connection-state"), url=$("#server-url"), statusBox=$("#connection-status"), cv=$("#connection-view"), lv=$("#login-view"), wv=$("#workspace-view"), list=$("#patient-list"), search=$("#patient-search"), patientStatus=$("#patient-status"), dialog=$("#patient-dialog");
function status(el,msg,kind=""){el.textContent=msg;el.className=`status-box ${kind}`.trim()}
function toggle(el,show){el.classList.toggle("hidden",!show)}
function showConnectionBanner(message,kind="error"){
 const banner=$("#runtime-status");
 if(!banner)return;
 status(banner,message,kind);
 banner.classList.remove("hidden");
}
function hideConnectionBanner(){
 const banner=$("#runtime-status");
 if(banner)banner.classList.add("hidden");
}
function enterSignedOutState(message="Please sign in again."){
 clearAccessToken();
 currentUserProfile=null;
 sessionStorage.removeItem("hhms.current_user");
 applyNavigationAccess(null);
 applyRecordAccess(null);
 toggle(wv,false);
 toggle(lv,true);
 toggle(cv,false);
 status($("#login-status"),message,"error");
}

let currentUserProfile=null;
async function loadUserProfile(){
 try{
  currentUserProfile=await getCurrentUserProfile();
  sessionStorage.setItem("hhms.current_user",JSON.stringify(currentUserProfile));
  applyNavigationAccess(currentUserProfile);applyRecordAccess(currentUserProfile);
  const badge=$("#user-badge");
  if(badge)badge.textContent=currentUserProfile.full_name||currentUserProfile.username||"User";
 }catch(e){
  currentUserProfile=null;
  sessionStorage.removeItem("hhms.current_user");
  applyNavigationAccess(null);applyRecordAccess(null);
  throw e;
 }
}
function restoreUserProfile(){
 try{const raw=sessionStorage.getItem("hhms.current_user");if(raw){currentUserProfile=JSON.parse(raw);applyNavigationAccess(currentUserProfile);applyRecordAccess(currentUserProfile);}}catch{sessionStorage.removeItem("hhms.current_user")}
}
async function connectTo(base){try{const normalized=setServerBaseUrl(base);state.textContent="Checking";status(statusBox,"Checking HHMS server…");const h=await checkServer(normalized);$("#server-name").textContent=h.service||"HHMS Server";$("#server-version").textContent=h.version||"—";$("#server-address").textContent=normalized;$("#server-details").classList.remove("hidden");status(statusBox,"HHMS server is online.","success");state.textContent="Connected";toggle(cv,false);toggle(lv,!getAccessToken());toggle(wv,!!getAccessToken());if(getAccessToken()){await loadUserProfile();await loadPatientList();}}catch(e){state.textContent="Offline";status(statusBox,e instanceof Error?e.message:"Unable to connect to HHMS server.","error")}}
async function discover(){try{status(statusBox,"Searching for HHMS server…");state.textContent="Searching";const found=await discoverServer();if(!found)throw new Error("HHMS server was not found. Enter the server address manually.");url.value=found;await connectTo(found)}catch(e){state.textContent="Offline";status(statusBox,e instanceof Error?e.message:"Unable to discover HHMS server.","error")}}
async function loadPatientList(){try{status(patientStatus,"Loading patients…");const rows=await listPatients(search.value);list.replaceChildren(...rows.map(patientCard));status(patientStatus,rows.length?`${rows.length} patient(s) loaded.`:"No patients found.",rows.length?"success":"")}catch(e){status(patientStatus,e instanceof Error?e.message:"Unable to load patients.","error")}}
function patientCard(p){const el=document.createElement("button");el.className="patient-card";el.type="button";const age=p.age??"—";el.innerHTML=`<strong>${escapeHtml(nameOf(p))}</strong><span>${escapeHtml(p.patient_number||"—")} · ${escapeHtml(p.gender||"—")} · Age ${escapeHtml(String(age))}</span><span>${escapeHtml(p.mobile_number||"No mobile")}</span>`;el.addEventListener("click",()=>openPatient(p.id));return el}
function nameOf(p){return [p.first_name,p.middle_name,p.last_name].filter(Boolean).join(" ")||"Unnamed patient"}
function escapeHtml(v){return String(v).replace(/[&<>'"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[c]))}
function rememberRecentPatient(id){const key="hhms.recent_patients";let ids=[];try{ids=JSON.parse(sessionStorage.getItem(key)||"[]")}catch{};ids=[String(id),...ids.filter(x=>String(x)!==String(id))].slice(0,5);sessionStorage.setItem(key,JSON.stringify(ids))}\nasync function openPatient(id){try{const p=await getPatient(id);rememberRecentPatient(p.id);$("#detail-name").textContent=nameOf(p);$("#detail-meta").textContent=`Patient ID ${p.id}`;$("#detail-number").textContent=p.patient_number||"—";$("#detail-gender").textContent=p.gender||"—";$("#detail-dob").textContent=p.date_of_birth||"—";$("#detail-mobile").textContent=p.mobile_number||"—";window.currentPatient=p;applyRecordAccess(currentUserProfile);toggle($("#patient-detail"),true);toggle($(".content-panel"),false);renderRecordView("overview",p);}catch(e){status(patientStatus,e instanceof Error?e.message:"Unable to load patient.","error")}}
async function renderRecordView(view,p){const box=$("#record-view");const tab=document.querySelector(`.record-tab[data-record-view="${view}"]`);if(tab?.disabled||tab?.classList.contains("hidden")){box.innerHTML="<div class=\"empty-state\">You do not have permission to open this section.</div>";return;}$(".record-tab.active")?.classList.remove("active");document.querySelector(`.record-tab[data-record-view="${view}"]`)?.classList.add("active");if(view==="clinical"){await openClinicalWorkspace(p,box);return}if(view==="ipd"){await openIPDWorkspace(p,box);return}if(view==="investigations"){await openInvestigationsWorkspace(p,box);return}if(view==="billing"){await openBillingWorkspace(p,box);return}if(view==="mrd"){await openMRDWorkspace(p,box);return}if(view==="reports"){await openReportsWorkspace(box,p);return}if(view==="overview"){await openPatientTimeline(box,p);return}const descriptions={overview:"Patient timeline.",billing:"Billing workspace.",mrd:"MRD workspace."};box.innerHTML=`<h3>${view[0].toUpperCase()+view.slice(1)}</h3><p>${descriptions[view]||"Module not yet available."}</p>`}
function closePatientDetail(){toggle($("#patient-detail"),false);toggle($(".content-panel"),true)}
$("#discover").addEventListener("click",discover);$("#connect").addEventListener("click",()=>url.value.trim()?connectTo(url.value.trim()):status(statusBox,"Enter a server address or use Discover Server.","error"));$("#clear").addEventListener("click",()=>{clearSavedServer();url.value="";status(statusBox,"Saved server address cleared.")});$("#login-form").addEventListener("submit",async e=>{e.preventDefault();try{status($("#login-status"),"Signing in…");const fd=new FormData(e.currentTarget);await login(fd.get("username"),fd.get("password"));await loadUserProfile();toggle(lv,false);toggle(wv,true);await loadPatientList();}catch(err){status($("#login-status"),err instanceof Error?err.message:"Unable to sign in.","error")}});$("#logout").addEventListener("click",()=>{clearAccessToken();sessionStorage.removeItem("hhms.current_user");location.reload()});$("#patient-search-button").addEventListener("click",loadPatientList);search.addEventListener("keydown",e=>{if(e.key==="Enter")loadPatientList()});$("#patient-back").addEventListener("click",closePatientDetail);$("#new-patient").addEventListener("click",()=>{dialog.showModal();status($("#create-patient-status"),"")});$("#close-patient-dialog").addEventListener("click",()=>dialog.close());$("#patient-form").addEventListener("submit",async e=>{e.preventDefault();const fd=new FormData(e.currentTarget);const payload=Object.fromEntries(fd.entries());for(const k of Object.keys(payload))if(payload[k]==="")delete payload[k];try{status($("#create-patient-status"),"Saving patient…");const p=await createPatient(payload);dialog.close();search.value=p.patient_number||"";await loadPatientList();await openPatient(p.id);}catch(err){status($("#create-patient-status"),err instanceof Error?err.message:"Unable to register patient.","error")}});document.querySelectorAll(".record-tab").forEach(b=>b.addEventListener("click",async()=>{await renderRecordView(b.dataset.recordView,window.currentPatient)}));window.addEventListener("hhms:open-patient",e=>openPatient(e.detail.patientId));window.addEventListener("hhms:open-patient-clinical",async e=>{try{await openPatient(e.detail.patientId);await renderRecordView("clinical",window.currentPatient);}catch(err){status(patientStatus,err instanceof Error?err.message:"Unable to open clinical workspace.","error");}});window.addEventListener("hhms:auth-expired",()=>enterSignedOutState("Your HHMS session has expired. Please sign in again."));
window.addEventListener("hhms:request-timeout",()=>{showConnectionBanner("A server request timed out. The connection may be slow or unavailable.","warning")});
window.addEventListener("hhms:server-state",e=>{if(e.detail?.online){state.textContent="Connected";hideConnectionBanner();}else{state.textContent="Offline";showConnectionBanner("HHMS server connection lost. Changes cannot be saved until the server is reachable.","error");}});
window.addEventListener("offline",()=>{state.textContent="Offline";showConnectionBanner("Network connection is unavailable. HHMS will reconnect when the LAN is available.","error")});
window.addEventListener("online",async()=>{state.textContent="Checking";showConnectionBanner("Network restored. Checking HHMS server…");if(serverBaseUrlSafe())try{await checkServer();hideConnectionBanner();state.textContent="Connected";}catch{}else hideConnectionBanner();});
function serverBaseUrlSafe(){try{return !!loadClientConfig().manualServerUrl||!!getServerBaseUrl()}catch{return false}}
document.querySelectorAll(".nav-item[data-app-view]").forEach(b=>b.addEventListener("click",async()=>{document.querySelectorAll(".nav-item[data-app-view]").forEach(x=>x.classList.remove("active"));b.classList.add("active");const gv=document.querySelector("#global-view");toggle(gv,true);document.querySelectorAll(".content-panel").forEach(x=>{if(x.id!=="global-view")x.classList.add("hidden")});if(b.dataset.appView==="dashboard"){await openDashboard(gv,{patient:window.currentPatient||null});}else if(b.dataset.appView==="opd"){await openOPDQueueWorkspace(gv);}
else if(b.dataset.appView==="statistics"){await openStatisticsWorkspace(gv);}else if(b.dataset.appView==="reports"){await openReportsWorkspace(gv,window.currentPatient||null);}else if(b.dataset.appView==="inventory"){await openInventoryWorkspace(gv);}else if(b.dataset.appView==="procurement"){await openProcurementWorkspace(gv);}else if(b.dataset.appView==="activity"){await openActivityWorkspace(gv);}else if(b.dataset.appView==="administration"){await openAdministrationWorkspace(gv);}else if(b.dataset.appView==="settings"){await openSettingsWorkspace(gv);}else if(b.dataset.appView==="system-health"){const m=await import("./system_health.js");await m.openSystemHealthWorkspace(gv);}else if(b.dataset.appView==="historical"){await openHistoricalWorkspace(gv,window.currentPatient||null);}
else if(b.dataset.appView==="patients"){toggle($("#global-view"),false);document.querySelectorAll(".content-panel").forEach(x=>{if(x.id!=="global-view")x.classList.add("hidden")});toggle($(".content-panel"),true);}}));restoreUserProfile();(async()=>{const c=loadClientConfig();if(c.manualServerUrl){url.value=c.manualServerUrl;await connectTo(c.manualServerUrl);}else{await discover();}})();

import("./system_health.js").then(()=>{}).catch(()=>{});
import("./pharmacy.js").then(m=>m.initPharmacyWorkspace()).catch(()=>{});
