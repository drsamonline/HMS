import{discoverServer}from"./discovery.js";
import{checkServer,setServerBaseUrl,login,listPatients,getPatient,createPatient,listCaseRecords,getCaseRecord,createCaseRecord,updateCaseRecord,getAccessToken,clearAccessToken}from"./api.js";
import{clearSavedServer,loadClientConfig}from"./config.js";

const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];
const state=$("#connection-state"),url=$("#server-url"),statusBox=$("#connection-status"),cv=$("#connection-view"),lv=$("#login-view"),wv=$("#workspace-view"),list=$("#patient-list"),search=$("#patient-search"),patientStatus=$("#patient-status"),dialog=$("#patient-dialog"),casePanel=$("#case-panel");
let activePatient=null, activeCase=null;

function status(el,msg,kind=""){el.textContent=msg;el.className=`status-box ${kind}`.trim()}
function toggle(el,show){el.classList.toggle("hidden",!show)}
function nameOf(p){return[p.first_name,p.middle_name,p.last_name].filter(Boolean).join(" ")||"Unnamed patient"}
function escapeHtml(v){return String(v??"").replace(/[&<>'"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]))}

async function connectTo(base){
  try{
    const normalized=setServerBaseUrl(base); state.textContent="Checking"; status(statusBox,"Checking HHMS server…");
    const h=await checkServer(normalized);
    $("#server-name").textContent=h.service||"HHMS Server"; $("#server-version").textContent=h.version||"—"; $("#server-address").textContent=normalized;
    $("#server-details").classList.remove("hidden"); status(statusBox,"HHMS server is online.","success"); state.textContent="Connected";
    toggle(cv,false); toggle(lv,!getAccessToken()); toggle(wv,!!getAccessToken()); if(getAccessToken())await loadPatientList();
  }catch(e){state.textContent="Offline";status(statusBox,e instanceof Error?e.message:"Unable to connect to HHMS server.","error")}
}
async function discover(){
  try{status(statusBox,"Searching for HHMS server…");state.textContent="Searching";const found=await discoverServer();if(!found)throw new Error("HHMS server was not found. Enter the server address manually.");url.value=found;await connectTo(found)}
  catch(e){state.textContent="Offline";status(statusBox,e instanceof Error?e.message:"Unable to discover HHMS server.","error")}
}
async function loadPatientList(){
  try{status(patientStatus,"Loading patients…");const rows=await listPatients(search.value);list.replaceChildren(...rows.map(patientCard));status(patientStatus,rows.length?`${rows.length} patient(s) loaded.`:"No patients found.",rows.length?"success":"")}
  catch(e){status(patientStatus,e instanceof Error?e.message:"Unable to load patients.","error")}
}
function patientCard(p){
  const el=document.createElement("button");el.className="patient-card";el.type="button";
  el.innerHTML=`<strong>${escapeHtml(nameOf(p))}</strong><span>${escapeHtml(p.patient_number||"—")} · ${escapeHtml(p.gender||"—")} · Age ${escapeHtml(p.age??"—")}</span><span>${escapeHtml(p.mobile_number||"No mobile")}</span>`;
  el.addEventListener("click",()=>openPatient(p.id));return el;
}
async function openPatient(id){
  try{
    activePatient=await getPatient(id);activeCase=null;
    $("#detail-name").textContent=nameOf(activePatient);$("#detail-meta").textContent=`Patient ID ${activePatient.id}`;
    $("#detail-number").textContent=activePatient.patient_number||"—";$("#detail-gender").textContent=activePatient.gender||"—";$("#detail-dob").textContent=activePatient.date_of_birth||"—";$("#detail-mobile").textContent=activePatient.mobile_number||"—";
    toggle($("#patient-detail"),true);toggle($(".content-panel"),false);renderRecordView("overview");
  }catch(e){status(patientStatus,e instanceof Error?e.message:"Unable to load patient.","error")}
}
function renderRecordView(view){
  const box=$("#record-view");
  $$(".record-tab").forEach(b=>b.classList.toggle("active",b.dataset.recordView===view));
  if(view==="clinical") return loadClinicalWorkspace();
  const descriptions={overview:"Patient demographic information and registration are available.",ipd:"IPD workspace will connect to admissions and IPD clinical records.",billing:"Billing workspace will connect to invoices, payments and balances.",mrd:"MRD workspace will connect to patient-file and archive records."};
  box.innerHTML=`<div class="module-placeholder"><h3>${view[0].toUpperCase()+view.slice(1)}</h3><p>${descriptions[view]||"Module view."}</p></div>`;
}
async function loadClinicalWorkspace(){
  const box=$("#record-view");
  box.innerHTML=`<div class="clinical-workspace"><div class="clinical-toolbar"><div><h3>Homoeopathic Case Record</h3><p>Compact structured selections with free-text clinical narrative.</p></div><button id="new-case" class="primary">New Case</button></div><div id="case-status" class="status-box"></div><div id="case-list" class="case-list"></div><form id="case-form" class="case-form hidden"><div class="case-form-header"><div><h3 id="case-form-title">New Case</h3><span id="case-number" class="case-number"></span></div><div class="button-row"><button type="button" id="case-cancel" class="secondary">Cancel</button><button type="submit" class="primary">Save Case</button></div></div><div id="case-save-status" class="status-box"></div>${caseFormHtml()}</form></div>`;
  $("#new-case").addEventListener("click",()=>openCaseForm(null));
  await loadCaseList();
}
async function loadCaseList(){
  const listBox=$("#case-list"), box=$("#case-status");
  try{
    const cases=await listCaseRecords(activePatient.id);
    if(!cases.length){listBox.innerHTML='<div class="empty-state">No case records yet. Create the first case.</div>';status(box,"");return}
    listBox.replaceChildren(...cases.map(c=>{const b=document.createElement("button");b.type="button";b.className="case-card";b.innerHTML=`<strong>${escapeHtml(c.case_number)}</strong><span>${escapeHtml(c.case_status)}</span><span>${escapeHtml(new Date(c.updated_at).toLocaleString())}</span>`;b.onclick=()=>openCaseForm(c.id);return b}));
    status(box,`${cases.length} case record(s) loaded.`,"success");
  }catch(e){status(box,e instanceof Error?e.message:"Unable to load case records.","error")}
}
function caseFormHtml(){
  const textSections=[
    ["chief_complaints","Chief Complaints"],["history_present_illness","History of Present Illness"],["past_history","Past History"],["family_history","Family History"],["personal_history","Personal History"],["mental_generals","Mental Generals"],["physical_generals","Physical Generals"],["particulars","Particulars / LSMC"],["female_history","Female / Gynaecological History"],["male_history","Male History"],["sexual_reproductive_history","Sexual / Reproductive History"],["obstetric_history","Obstetric History"],["surgical_history","Surgical History"],["clinical_examination","Clinical Examination"],["characteristic_symptoms","Characteristic Symptoms"],["totality","Totality"],["miasmatic_assessment","Miasmatic Assessment"],["analytical_notes","Analytical Notes"],["remedy_differential","Remedy Differential"],["prescribing_rationale","Prescribing Rationale"]
  ];
  return `<section class="case-section"><h4>Case Status</h4><div class="compact-grid"><label>Status<select name="case_status"><option value="draft">Draft</option><option value="active">Active</option><option value="closed">Closed</option></select></label></div></section>
  <section class="case-section"><h4>Quick Generals</h4><div class="compact-grid">${["thermal","thirst","appetite","sleep","sweat","stool","urine","food_desires","food_aversions"].map(k=>`<label>${label(k)}<select data-qg="${k}">${quickOptions()}</select></label>`).join("")}</div></section>
  <section class="case-section"><h4>Modalities</h4><div class="modalities-grid">${["pressure","motion","rest","heat","cold","time","position","food","drinks","sleep"].map(k=>modalityControl(k)).join("")}</div></section>
  <section class="case-section"><h4>Detailed Case Taking</h4>${textSections.map(([k,l])=>`<label class="full-field">${l}<textarea name="${k}" rows="3"></textarea></label>`).join("")}</section>`;
}
function label(k){return k.replace(/_/g," ").replace(/\b\w/g,c=>c.toUpperCase())}
function quickOptions(){return'<option value="">Not recorded</option><option value="normal">Normal</option><option value="increased">Increased</option><option value="decreased">Decreased</option><option value="prefers_warm">Prefers warm</option><option value="prefers_cold">Prefers cold</option><option value="marked">Marked / peculiar</option>'}
function modalityControl(k){const id=`mod-${k}`;return`<div class="modality-card"><strong>${label(k)}</strong><div class="agg-amel"><label>Type<select data-mod-type="${k}"><option value="">—</option><option value="agg">Agg.</option><option value="amel">Amel.</option></select></label><label>Additional information<input data-mod-note="${k}" maxlength="500" placeholder="Enter qualifying detail"></label></div></div>`}
async function openCaseForm(id){
  const form=$("#case-form");form.classList.remove("hidden");status($("#case-save-status"),"");
  activeCase=id?await getCaseRecord(id):null;$("#case-form-title").textContent=activeCase?"Edit Case":"New Case";$("#case-number").textContent=activeCase?.case_number||"";
  form.reset();
  if(activeCase){form.elements.case_status.value=activeCase.case_status||"draft";for(const el of form.elements){if(el.name && el.name!=="case_status" && activeCase[el.name]!=null)el.value=activeCase[el.name]}const q=activeCase.quick_generals||{};$$("[data-qg]").forEach(el=>el.value=q[el.dataset.qg]||"");const m=activeCase.modalities||{};$$("[data-mod-type]").forEach(el=>el.value=m[el.dataset.modType]?.type||"");$$("[data-mod-note]").forEach(el=>el.value=m[el.dataset.modNote]?.additional||"");}
  form.scrollIntoView({behavior:"smooth",block:"start"});
}
function collectCasePayload(){
  const form=$("#case-form"), payload={patient_id:activePatient.id,case_status:form.elements.case_status.value};
  for(const el of form.elements)if(el.name && el.tagName!=="BUTTON" && el.name!=="case_status" && el.value.trim()!=="")payload[el.name]=el.value;
  const quick={};$$("[data-qg]").forEach(el=>{if(el.value)quick[el.dataset.qg]=el.value});payload.quick_generals=Object.keys(quick).length?quick:null;
  const modalities={};$$("[data-mod-type]").forEach(el=>{const key=el.dataset.modType,note=$(`[data-mod-note="${key}"]`).value.trim();if(el.value||note)modalities[key]={type:el.value||null,additional:note||null}});payload.modalities=Object.keys(modalities).length?modalities:null;
  return payload;
}
async function saveCase(e){
  e.preventDefault();try{status($("#case-save-status"),"Saving case…");const payload=collectCasePayload();activeCase=activeCase?await updateCaseRecord(activeCase.id,payload):await createCaseRecord(payload);status($("#case-save-status"),"Case saved successfully.","success");$("#case-number").textContent=activeCase.case_number;await loadCaseList();}catch(err){status($("#case-save-status"),err instanceof Error?err.message:"Unable to save case.","error")}}
function closePatientDetail(){toggle($("#patient-detail"),false);toggle($(".content-panel"),true)}
$("#discover").addEventListener("click",discover);$("#connect").addEventListener("click",()=>url.value.trim()?connectTo(url.value.trim()):status(statusBox,"Enter a server address or use Discover Server.","error"));
$("#clear").addEventListener("click",()=>{clearSavedServer();url.value="";status(statusBox,"Saved server address cleared.")});
$("#login-form").addEventListener("submit",async e=>{e.preventDefault();try{status($("#login-status"),"Signing in…");const fd=new FormData(e.currentTarget);await login(fd.get("username"),fd.get("password"));toggle(lv,false);toggle(wv,true);$("#user-badge").textContent=String(fd.get("username"));await loadPatientList()}catch(err){status($("#login-status"),err instanceof Error?err.message:"Unable to sign in.","error")}});
$("#logout").addEventListener("click",()=>{clearAccessToken();location.reload()});
$("#patient-search-button").addEventListener("click",loadPatientList);search.addEventListener("keydown",e=>{if(e.key==="Enter")loadPatientList()});
$("#patient-back").addEventListener("click",closePatientDetail);$("#new-patient").addEventListener("click",()=>{dialog.showModal();status($("#create-patient-status"),"")});$("#close-patient-dialog").addEventListener("click",()=>dialog.close());
$("#patient-form").addEventListener("submit",async e=>{e.preventDefault();const fd=new FormData(e.currentTarget),payload=Object.fromEntries(fd.entries());for(const k of Object.keys(payload))if(payload[k]==="")delete payload[k];try{status($("#create-patient-status"),"Saving patient…");const p=await createPatient(payload);dialog.close();search.value=p.patient_number||"";await loadPatientList();await openPatient(p.id)}catch(err){status($("#create-patient-status"),err instanceof Error?err.message:"Unable to register patient.","error")}});
document.addEventListener("click",e=>{const t=e.target.closest(".record-tab");if(t&&activePatient)renderRecordView(t.dataset.recordView)});
const c=loadClientConfig();if(c.manualServerUrl)url.value=c.manualServerUrl;discover();
