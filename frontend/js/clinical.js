import {
  listDiagnoses, createDiagnosis, updateDiagnosis, searchICD11,
  listFollowups, createFollowup,
  createPrescription, listMedicines, listCaseRecords, listVisits, createVisit,
  listDepartments, listDepartmentServices, listPrescriptionsByVisit, getCurrentUserProfile
} from "./api.js";

let clinicalState = { patient: null, caseRecord: null, diagnoses: [], followups: [], prescription: null, medicines: [], visits: [], visit: null, departments: [], services: [] };

export function initClinicalWorkspace() {
  window.hhmsClinical = { open: openClinicalWorkspace };
}

export async function openClinicalWorkspace(patient, host) {
  clinicalState.patient = patient;
  host.innerHTML = renderClinicalShell();
  wireClinicalShell(host);
  await refreshVisitSelector(host);
  await refreshCaseSelector(host);
}

function renderClinicalShell() {
  return `
    <section class="clinical-workspace">
      <header class="clinical-header">
        <div>
          <h2>Clinical Workspace</h2>
          <p id="clinical-patient-meta"></p>
        </div>
        <div class="clinical-actions">
          <select id="visit-selector"><option value="">Select visit</option></select>
          <button id="new-visit" class="secondary">New Visit</button>
          <select id="case-selector"><option value="">Select case</option></select>
          <button id="new-case" class="secondary">New Case</button>
          <button id="save-case" class="primary">Save Case</button>
        </div>
      </header>
      <div class="clinical-tabs" role="tablist">
        <button class="clinical-tab active" data-clinical-tab="case">Case</button>
        <button class="clinical-tab" data-clinical-tab="diagnosis">Diagnosis / ICD-11</button>
        <button class="clinical-tab" data-clinical-tab="prescription">Prescription</button>
        <button class="clinical-tab" data-clinical-tab="followup">Follow-up</button>
      </div>
      <div id="clinical-status" class="status-box"></div>
      <div id="clinical-panel"></div>
    </section>`;
}

function wireClinicalShell(host) {
  $("#visit-selector", host)?.addEventListener("change", async e => loadVisit(e.target.value, host));
  $("#new-visit", host)?.addEventListener("click", () => startNewVisit(host));
  $("#case-selector", host)?.addEventListener("change", async e => loadCase(e.target.value, host));
  $("#new-case", host)?.addEventListener("click", () => startNewCase(host));
  $("#save-case", host)?.addEventListener("click", () => saveCase(host));
  host.querySelectorAll(".clinical-tab").forEach(b => b.addEventListener("click", async () => {
    host.querySelector(".clinical-tab.active")?.classList.remove("active");
    b.classList.add("active");
    await renderTab(b.dataset.clinicalTab, host);
  }));
  renderPatientMeta(host);
  renderTab("case", host);
}

function renderPatientMeta(host) {
  const p = clinicalState.patient;
  $("#clinical-patient-meta", host).textContent = p ? `${nameOf(p)} · ${p.patient_number || "No registration number"}` : "";
}
function nameOf(p){ return [p?.first_name,p?.middle_name,p?.last_name].filter(Boolean).join(" ") || "Unnamed patient"; }
function escapeHtml(v){ return String(v ?? "").replace(/[&<>'"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c])); }
function setStatus(host,msg,kind=""){ const el=$("#clinical-status",host); el.textContent=msg; el.className=`status-box ${kind}`.trim(); }

async function refreshVisitSelector(host){
  try{
    clinicalState.visits=await listVisits(clinicalState.patient.id);
    const select=$("#visit-selector",host);
    select.replaceChildren(new Option("Select visit",""));
    clinicalState.visits.forEach(v=>select.add(new Option(`${v.visit_number} · ${new Date(v.visit_datetime).toLocaleString()} · ${v.case_type||""}`,String(v.id))));
    const preferred=clinicalState.caseRecord?.visit_id||clinicalState.visits[0]?.id;
    if(preferred){select.value=String(preferred);clinicalState.visit=clinicalState.visits.find(v=>String(v.id)===String(preferred))||null;}
    else startNewVisit(host);
  }catch(e){setStatus(host,e.message||"Unable to load visits.","error");}
}

function startNewVisit(host){
  clinicalState.visit={patient_id:clinicalState.patient.id,visit_type:"OPD",visit_datetime:new Date().toISOString(),consultation_status:"registered",case_type:"new",chief_complaint:""};
  renderVisitEditor(host);
}

async function loadVisit(id,host){
  clinicalState.visit=clinicalState.visits.find(v=>String(v.id)===String(id))||null;
  if(clinicalState.visit && clinicalState.caseRecord?.visit_id!==clinicalState.visit.id){
    const linked=clinicalState.visits.find(v=>v.id===clinicalState.caseRecord?.visit_id);
    if(linked) clinicalState.visit=linked;
  }
  renderVisitEditor(host);
}

function renderVisitEditor(host){
  const v=clinicalState.visit||{};
  const panel=$("#clinical-panel",host);
  if(!panel)return;
  panel.querySelector(".visit-editor")?.remove();
  panel.insertAdjacentHTML("afterbegin",`<div class="visit-editor content-panel"><h3>Encounter</h3><div class="case-toolbar"><label>Visit type<input id="visit-type" value="${escapeHtml(v.visit_type||"OPD")}"></label><label>Visit date/time<input id="visit-datetime" type="datetime-local" value="${toLocalDateTime(v.visit_datetime)}"></label><label>Case type<select id="visit-case-type"><option value="new" ${v.case_type==="new"?"selected":""}>New</option><option value="old" ${v.case_type==="old"?"selected":""}>Old</option></select></label></div><div class="case-toolbar"><label>Chief complaint<input id="visit-chief-complaint" value="${escapeHtml(v.chief_complaint||"")}"></label><button id="save-visit" class="secondary">Save Visit</button></div></div>`);
  $("#save-visit",host).addEventListener("click",()=>saveVisit(host));
}

function toLocalDateTime(value){const d=new Date(value||Date.now());const pad=n=>String(n).padStart(2,"0");return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;}

async function saveVisit(host){
  try{
    const profile=await getCurrentUserProfile();
    const payload={patient_id:clinicalState.patient.id,visit_type:$("#visit-type",host).value.trim()||"OPD",visit_datetime:new Date($("#visit-datetime",host).value).toISOString(),chief_complaint:$("#visit-chief-complaint",host).value.trim()||null,consultation_status:"registered",consulting_doctor_id:Number(profile?.id||profile?.user?.id||profile?.sub),case_type:$("#visit-case-type",host).value};
    clinicalState.visit=await createVisit(payload);
    setStatus(host,`Visit ${clinicalState.visit.visit_number} saved.`,"success");
    await refreshVisitSelector(host);
    startNewCase(host);
    renderTab("case",host);
  }catch(e){setStatus(host,e.message||"Unable to save visit.","error");}
}

async function refreshCaseSelector(host){
  if(!clinicalState.patient) return;
  try{
    const cases=await listCaseRecords(clinicalState.patient.id);
    const select=$("#case-selector",host); select.replaceChildren(new Option("Select case",""));
    cases.forEach(c=>select.add(new Option(`${c.case_number} · ${c.case_status}`,String(c.id))));
    if(cases[0]){ select.value=String(cases[0].id); await loadCase(cases[0].id,host); }
    else startNewCase(host);
  }catch(e){setStatus(host,e.message||"Unable to load cases.","error");}
}
async function loadCase(id,host){
  if(!id){startNewCase(host);return;}
  try{
    const cases=await listCaseRecords(clinicalState.patient.id); const found=cases.find(c=>String(c.id)===String(id));
    clinicalState.caseRecord=found||null;
    if(clinicalState.caseRecord?.visit_id){
      clinicalState.visit=clinicalState.visits.find(v=>String(v.id)===String(clinicalState.caseRecord.visit_id))||clinicalState.visit;
      const visitSelect=$("#visit-selector",host); if(visitSelect&&clinicalState.visit) visitSelect.value=String(clinicalState.visit.id);
    }
    await loadRelated(host); await renderTab(host.querySelector(".clinical-tab.active")?.dataset.clinicalTab||"case",host);
  }catch(e){setStatus(host,e.message||"Unable to load case.","error");}
}
function startNewCase(host){
  clinicalState.caseRecord={patient_id:clinicalState.patient.id,visit_id:clinicalState.visit?.id||null,case_status:"draft",quick_generals:{},modalities:{}};
  clinicalState.diagnoses=[]; clinicalState.followups=[]; clinicalState.prescription=null;
  setStatus(host,"New draft case ready.");
  renderTab("case",host);
}
async function loadRelated(host){
  if(!clinicalState.caseRecord?.id)return;
  try{
    clinicalState.diagnoses=await listDiagnoses(clinicalState.caseRecord.id);
    clinicalState.followups=await listFollowups(clinicalState.caseRecord.id);
  }catch(e){setStatus(host,e.message||"Unable to load related clinical records.","error");}
}
function val(field){ return clinicalState.caseRecord?.[field] ?? ""; }
function textarea(name,label){ return `<label>${escapeHtml(label)}<textarea data-case-field="${escapeHtml(name)}" rows="4">${escapeHtml(val(name))}</textarea></label>`; }
function renderCase(host){
  const c=clinicalState.caseRecord||{};
  $("#clinical-panel",host).innerHTML=`
  <div class="case-toolbar">
    <label>Status<select data-case-field="case_status"><option value="draft" ${c.case_status==="draft"?"selected":""}>Draft</option><option value="active" ${c.case_status==="active"?"selected":""}>Active</option><option value="closed" ${c.case_status==="closed"?"selected":""}>Closed</option></select></label>
  </div>
  <div class="case-grid">
    ${textarea("chief_complaints","Chief Complaints")}
    ${textarea("history_present_illness","History of Present Illness")}
    ${textarea("past_history","Past History")}
    ${textarea("family_history","Family History")}
    ${textarea("personal_history","Personal History")}
    ${textarea("mental_generals","Mental Generals")}
    ${textarea("physical_generals","Physical Generals")}
    ${textarea("particulars","Particulars / LSMC")}
    ${textarea("female_history","Female / Gynaecological History")}
    ${textarea("male_history","Male History")}
    ${textarea("sexual_reproductive_history","Sexual / Reproductive History")}
    ${textarea("obstetric_history","Obstetric History")}
    ${textarea("surgical_history","Surgical History")}
    ${textarea("clinical_examination","Clinical Examination")}
    ${textarea("characteristic_symptoms","Characteristic Symptoms")}
    ${textarea("totality","Totality")}
    ${textarea("miasmatic_assessment","Miasmatic Assessment")}
    ${textarea("analytical_notes","Analytical Notes")}
    ${textarea("remedy_differential","Remedy Differential")}
    ${textarea("prescribing_rationale","Prescribing Rationale")}
  </div>
  <div class="structured-row">
    <label>Quick Generals JSON<textarea id="quick-generals" rows="5">${escapeHtml(JSON.stringify(c.quick_generals||{},null,2))}</textarea></label>
    <label>Modalities JSON<textarea id="modalities" rows="5">${escapeHtml(JSON.stringify(c.modalities||{},null,2))}</textarea></label>
  </div>`;
}
function collectCase(host){
  const c={...clinicalState.caseRecord};
  host.querySelectorAll("[data-case-field]").forEach(el=>{ c[el.dataset.caseField]=el.value; });
  try{ c.quick_generals=JSON.parse($("#quick-generals",host).value||"{}"); }catch{ throw new Error("Quick Generals must contain valid JSON."); }
  try{ c.modalities=JSON.parse($("#modalities",host).value||"{}"); }catch{ throw new Error("Modalities must contain valid JSON."); }
  for(const k of Object.keys(c)) if(c[k]===""||c[k]===null) delete c[k];
  return c;
}
async function saveCase(host){
  try{
    const c=collectCase(host); let saved;
    if(c.id){ saved=await (await import("./api.js")).updateCaseRecord(c.id,c); }
    else { saved=await (await import("./api.js")).createCaseRecord({patient_id:clinicalState.patient.id,case_status:c.case_status||"draft",...c}); }
    clinicalState.caseRecord=saved; setStatus(host,"Case saved successfully.","success"); await refreshCaseSelector(host);
  }catch(e){setStatus(host,e.message||"Unable to save case.","error");}
}
async function renderTab(tab,host){
  if(tab==="case") return renderCase(host);
  if(!clinicalState.caseRecord?.id){ $("#clinical-panel",host).innerHTML=`<div class="empty-state">Save the case first to manage diagnosis, prescription, or follow-up.</div>`; return; }
  if(tab==="diagnosis") return renderDiagnosis(host);
  if(tab==="prescription") return renderPrescription(host);
  if(tab==="followup") return renderFollowup(host);
}
function renderDiagnosis(host){
  const rows=clinicalState.diagnoses;
  $("#clinical-panel",host).innerHTML=`<div class="clinical-two-col">
    <div><h3>Diagnoses</h3><div id="diagnosis-list">${rows.map(d=>`<article class="record-card"><strong>${escapeHtml(d.diagnosis_name)}</strong><span>${escapeHtml(d.diagnosis_type)} ${d.icd11_code?`· ICD-11 ${escapeHtml(d.icd11_code)}`:""}</span><small>${escapeHtml(d.icd11_title||"")}</small></article>`).join("")||'<div class="empty-state">No diagnosis recorded.</div>'}</div></div>
    <form id="diagnosis-form" class="compact-form"><h3>Add Diagnosis</h3>
      <label>Name<input name="diagnosis_name" required maxlength="200"></label>
      <label>Type<select name="diagnosis_type"><option>clinical</option><option>provisional</option><option>differential</option><option>confirmed</option><option>other</option></select></label>
      <label>ICD-11 Search<input id="icd-search" name="icd_search" placeholder="Type ≥2 characters"></label>
      <div id="icd-results" class="search-results"></div>
      <label>Notes<textarea name="notes" rows="3"></textarea></label>
      <label><input type="checkbox" name="is_primary"> Primary diagnosis</label>
      <button class="primary" type="submit">Save Diagnosis</button>
    </form></div>`;
  $("#icd-search",host).addEventListener("input",async e=>{const q=e.target.value.trim(); if(q.length<2){$("#icd-results",host).replaceChildren();return;} try{const rows=await searchICD11(q); $("#icd-results",host).innerHTML=rows.map(r=>`<button type="button" data-code="${escapeHtml(r.code||"")}" data-title="${escapeHtml(r.title)}" data-uri="${escapeHtml(r.uri||"")}" data-release="${escapeHtml(r.release)}">${escapeHtml(r.code||"")} · ${escapeHtml(r.title)}</button>`).join("")||"<small>No ICD-11 results.</small>"; $("#icd-results",host).querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>{ $("#diagnosis-form input[name=diagnosis_name]").value=b.dataset.title; $("#diagnosis-form").dataset.icdCode=b.dataset.code; $("#diagnosis-form").dataset.icdTitle=b.dataset.title; $("#diagnosis-form").dataset.icdUri=b.dataset.uri; $("#diagnosis-form").dataset.icdRelease=b.dataset.release; $("#icd-results",host).replaceChildren(); })); }catch(err){setStatus(host,err.message||"ICD-11 search failed.","error");}});
  $("#diagnosis-form",host).addEventListener("submit",async e=>{e.preventDefault(); const f=new FormData(e.currentTarget); const form=e.currentTarget; const payload={case_record_id:clinicalState.caseRecord.id,patient_id:clinicalState.patient.id,visit_id:clinicalState.visit?.id||null,diagnosis_name:f.get("diagnosis_name"),diagnosis_type:f.get("diagnosis_type"),notes:f.get("notes")||null,is_primary:f.get("is_primary")==="on",icd11_code:form.dataset.icdCode||null,icd11_title:form.dataset.icdTitle||null,icd11_uri:form.dataset.icdUri||null,icd11_release:form.dataset.icdRelease||null}; try{await createDiagnosis(payload); clinicalState.diagnoses=await listDiagnoses(clinicalState.caseRecord.id); setStatus(host,"Diagnosis saved.","success"); renderDiagnosis(host);}catch(err){setStatus(host,err.message||"Unable to save diagnosis.","error");}});
}
async function renderFollowup(host){
  const rows=clinicalState.followups;
  $("#clinical-panel",host).innerHTML=`<div class="clinical-two-col"><div><h3>Follow-ups</h3><div>${rows.map(f=>`<article class="record-card"><strong>${escapeHtml(new Date(f.followup_datetime).toLocaleString())}</strong><span>General: ${escapeHtml(f.general_status||"—")} · Remedy: ${escapeHtml(f.remedy_response||"—")}</span><small>${escapeHtml(f.clinical_assessment||"")}</small></article>`).join("")||'<div class="empty-state">No follow-up recorded.</div>'}</div></div><form id="followup-form" class="compact-form"><h3>Record Follow-up</h3><label>Date/time<input type="datetime-local" name="followup_datetime" required></label><label>General status<select name="general_status"><option value="">—</option><option>better</option><option>same</option><option>worse</option></select></label><label>Mental status<select name="mental_status"><option value="">—</option><option>better</option><option>same</option><option>worse</option></select></label><label>Particular status<select name="particular_status"><option value="">—</option><option>better</option><option>same</option><option>worse</option></select></label><label>Remedy response<select name="remedy_response"><option value="">—</option><option>good</option><option>partial</option><option>none</option><option>aggravation</option><option>unclear</option></select></label><label>Decision<select name="decision"><option value="">—</option><option>wait</option><option>repeat</option><option>change_remedy</option><option>stop_reassess</option></select></label><label>New symptoms<textarea name="new_symptoms" rows="2"></textarea></label><label>Old symptoms<textarea name="old_symptoms" rows="2"></textarea></label><label>Clinical assessment<textarea name="clinical_assessment" rows="3"></textarea></label><label>Notes<textarea name="notes" rows="2"></textarea></label><button class="primary">Save Follow-up</button></form></div>`;
  $("#followup-form",host).addEventListener("submit",async e=>{e.preventDefault();const f=new FormData(e.currentTarget);const clean={}; for(const [k,v] of f.entries())if(v)clean[k]=k==="followup_datetime"?new Date(v).toISOString():v; try{await createFollowup({case_record_id:clinicalState.caseRecord.id,patient_id:clinicalState.patient.id,visit_id:clinicalState.visit?.id||null,...clean});clinicalState.followups=await listFollowups(clinicalState.caseRecord.id);setStatus(host,"Follow-up saved.","success");renderFollowup(host);}catch(err){setStatus(host,err.message||"Unable to save follow-up.","error");}});
}
async function renderPrescription(host){
  try{clinicalState.prescription=(clinicalState.visit?.id?(await listPrescriptionsByVisit(clinicalState.visit.id))[0]||null):null;}catch{clinicalState.prescription=null;}
  if(!clinicalState.medicines.length){ try{clinicalState.medicines=await listMedicines("");}catch{clinicalState.medicines=[];} }
  $("#clinical-panel",host).innerHTML=`<div class="clinical-two-col"><div><h3>Prescription</h3>${clinicalState.prescription?`<article class="record-card"><strong>${escapeHtml(clinicalState.prescription.prescription_number)}</strong><span>${escapeHtml(clinicalState.prescription.diagnosis||"")}</span>${(clinicalState.prescription.items||[]).map(i=>`<small>${escapeHtml(i.medicine_id)} · ${escapeHtml(i.dosage)} · ${escapeHtml(i.frequency)} · Qty ${escapeHtml(i.quantity)}</small>`).join("")}</article>`:'<div class="empty-state">Select or create a prescription for this visit.</div>'}</div><form id="prescription-form" class="compact-form"><h3>Create Prescription</h3><label>Visit<input value="${escapeHtml(clinicalState.visit?.visit_number||"Select a visit")}" disabled></label><label>Date/time<input type="datetime-local" name="prescription_datetime" required></label><label>Diagnosis<textarea name="diagnosis" rows="2"></textarea></label><label>Clinical notes<textarea name="clinical_notes" rows="2"></textarea></label><label>Treatment plan<textarea name="treatment_plan" rows="2"></textarea></label><div id="rx-items"></div><button type="button" id="add-rx-item">Add medicine</button><button class="primary">Create Prescription</button></form></div>`;
  const itemsHost=$("#rx-items",host); const add=()=>{const idx=itemsHost.children.length; const el=document.createElement("fieldset"); el.className="rx-item"; el.innerHTML=`<legend>Medicine ${idx+1}</legend><label>Medicine<select name="medicine_id">${clinicalState.medicines.map(m=>`<option value="${m.id}">${escapeHtml(m.medicine_name)} · ${escapeHtml(m.medicine_code)}</option>`).join("")}</select></label><label>Dosage<input name="dosage" required maxlength="100"></label><label>Frequency<input name="frequency" required maxlength="100"></label><label>Duration days<input type="number" name="duration_days" min="1"></label><label>Quantity<input type="number" name="quantity" min="0.01" step="0.01" required></label><label>Instructions<textarea name="instructions" rows="2"></textarea></label>`;itemsHost.appendChild(el);}; add(); $("#add-rx-item",host).addEventListener("click",add);
  $("#prescription-form",host).addEventListener("submit",async e=>{e.preventDefault();const f=new FormData(e.currentTarget);const itemNodes=[...itemsHost.querySelectorAll(".rx-item")];const items=itemNodes.map(n=>{const get=k=>n.querySelector(`[name=${k}]`)?.value||"";return {medicine_id:Number(get("medicine_id")),dosage:get("dosage"),frequency:get("frequency"),duration_days:get("duration_days")?Number(get("duration_days")):null,quantity:Number(get("quantity")),instructions:get("instructions")||null};});const profile=await getCurrentUserProfile(); const payload={visit_id:Number(clinicalState.visit?.id),prescribed_by:Number(profile?.id||profile?.user?.id||profile?.sub),prescription_datetime:new Date(f.get("prescription_datetime")).toISOString(),diagnosis:f.get("diagnosis")||null,clinical_notes:f.get("clinical_notes")||null,treatment_plan:f.get("treatment_plan")||null,items}; try{clinicalState.prescription=await createPrescription(payload);setStatus(host,"Prescription created.","success");renderPrescription(host);}catch(err){setStatus(host,err.message||"Unable to create prescription.","error");}});
}
