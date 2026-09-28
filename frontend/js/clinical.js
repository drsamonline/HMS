import {
  listDiagnoses, createDiagnosis, updateDiagnosis, searchICD11,
  listFollowups, createFollowup,
  createPrescription, getPrescription, listMedicines,
  listCaseRecords, renewCurrentYearCase
} from "./api.js";

let clinicalState = { patient: null, caseRecord: null, diagnoses: [], followups: [], prescription: null, medicines: [] };

export function initClinicalWorkspace() {
  window.hhmsClinical = { open: openClinicalWorkspace };
}

export async function openClinicalWorkspace(patient, host) {
  clinicalState.patient = patient;
  host.innerHTML = renderClinicalShell();
  wireClinicalShell(host);
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
          <select id="case-selector"><option value="">Select case</option></select>
          <button id="new-case" class="primary">New Case</button>
          <button id="save-case" class="primary">Save Case</button>
        </div>
      </header>
      <div class="clinical-tabs" role="tablist">
        <button class="clinical-tab active" data-clinical-tab="case">Case</button>
        <button class="clinical-tab" data-clinical-tab="diagnosis">Diagnosis / ICD-11</button>
        <button class="clinical-tab" data-clinical-tab="prescription">Prescription</button>
        <button class="clinical-tab" data-clinical-tab="followup">Follow-up</button>
        <button class="clinical-tab" data-clinical-tab="pharmacy">Pharmacy</button>
      </div>
      <div id="clinical-status" class="status-box"></div>
      <div id="clinical-panel"></div>
    </section>`;
}

function wireClinicalShell(host) {
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

async function refreshCaseSelector(host){
  if(!clinicalState.patient) return;
  try{
    let cases=await listCaseRecords(clinicalState.patient.id);
    const thisYear=new Date().getFullYear();
    if(cases.length && Number(cases[0]?.case_year||0)<thisYear){ try { const renewed=await renewCurrentYearCase(clinicalState.patient.id, window.hhmsContext||{}); cases=[renewed,...cases.filter(c=>String(c.id)!==String(renewed.id))]; setStatus(host,`Case renewed for ${thisYear}.`); } catch {} }
    const select=$("#case-selector",host); select.replaceChildren(new Option("Select case",""));
    cases.forEach(c=>select.add(new Option(`${c.case_number} · ${c.case_year||"—"} · ${c.case_status}`,String(c.id))));
    if(cases[0]){ select.value=String(cases[0].id); await loadCase(cases[0].id,host); }
    else startNewCase(host);
  }catch(e){setStatus(host,e.message||"Unable to load cases.","error");}
}
async function loadCase(id,host){
  if(!id){startNewCase(host);return;}
  try{
    const cases=await listCaseRecords(clinicalState.patient.id); const found=cases.find(c=>String(c.id)===String(id));
    clinicalState.caseRecord=found||null; await loadRelated(host); await renderTab(host.querySelector(".clinical-tab.active")?.dataset.clinicalTab||"case",host);
  }catch(e){setStatus(host,e.message||"Unable to load case.","error");}
}
function startNewCase(host){
  clinicalState.caseRecord={patient_id:clinicalState.patient.id,case_status:"draft",quick_generals:{},modalities:{}};
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
  </div>
  <div class="modality-section">
    <h3>Homoeopathic Case Record — Modalities</h3>
    <p class="muted">Record each modality (e.g. heat, cold, motion) with its effect and additional detail.</p>
    <table class="modality-table"><thead><tr><th>Modality</th><th>Effect</th><th>Additional</th><th></th></tr></thead>
      <tbody id="modality-rows">${renderModalityRows(c.modalities||{})}</tbody>
    </table>
    <button type="button" id="add-modality" class="secondary">Add Modality</button>
  </div>`;
  wireModalityEditor(host);
}
function renderModalityRows(modalities){
  const entries=Object.entries(modalities||{});
  if(!entries.length) entries.push(["",""]);
  return entries.map(([name,value])=>{
    const effect=(value==="agg"||value==="amel")?value:(value&&typeof value==="object"?value.effect:"")||"";
    const additional=(value&&typeof value==="object"?value.additional:"")||"";
    return `<tr><td><input data-mod-name value="${escapeHtml(name)}" placeholder="e.g. heat"></td>
      <td><select data-mod-effect><option value="">—</option><option value="agg"${effect==="agg"?" selected":""}>Aggravated (agg)</option><option value="amel"${effect==="amel"?" selected":""}>Ameliorated (amel)</option></select></td>
      <td><input data-mod-note value="${escapeHtml(additional)}" placeholder="Additional detail"></td>
      <td><button type="button" class="remove-modality secondary">Remove</button></td></tr>`;
  }).join("");
}
function collectCase(host){
  const c={...clinicalState.caseRecord};
  host.querySelectorAll("[data-case-field]").forEach(el=>{ c[el.dataset.caseField]=el.value; });
  try{ c.quick_generals=JSON.parse($("#quick-generals",host).value||"{}"); }catch{ throw new Error("Quick Generals must contain valid JSON."); }
  const modalities={};
  host.querySelectorAll("#modality-rows tr").forEach(tr=>{
    const name=tr.querySelector("[data-mod-name]")?.value.trim()||"";
    if(!name) return;
    const effect=tr.querySelector("[data-mod-effect]")?.value||"";
    const additional=tr.querySelector("[data-mod-note]")?.value.trim()||"";
    modalities[name]={effect,additional};
  });
  c.modalities=modalities;
  for(const k of Object.keys(c)) if(c[k]===""||c[k]===null) delete c[k];
  return c;
}
function wireModalityEditor(host){
  $("#add-modality",host)?.addEventListener("click",()=>{
    const tbody=$("#modality-rows",host);
    tbody.insertAdjacentHTML("beforeend",renderModalityRows({}));
  });
  host.querySelectorAll(".remove-modality").forEach(b=>b.addEventListener("click",e=>e.target.closest("tr")?.remove()));
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
  $("#diagnosis-form",host).addEventListener("submit",async e=>{e.preventDefault(); const f=new FormData(e.currentTarget); const form=e.currentTarget; const payload={case_record_id:clinicalState.caseRecord.id,patient_id:clinicalState.patient.id,diagnosis_name:f.get("diagnosis_name"),diagnosis_type:f.get("diagnosis_type"),notes:f.get("notes")||null,is_primary:f.get("is_primary")==="on",icd11_code:form.dataset.icdCode||null,icd11_title:form.dataset.icdTitle||null,icd11_uri:form.dataset.icdUri||null,icd11_release:form.dataset.icdRelease||null}; try{await createDiagnosis(payload); clinicalState.diagnoses=await listDiagnoses(clinicalState.caseRecord.id); setStatus(host,"Diagnosis saved.","success"); renderDiagnosis(host);}catch(err){setStatus(host,err.message||"Unable to save diagnosis.","error");}});
}
async function renderFollowup(host){
  const rows=clinicalState.followups;
  $("#clinical-panel",host).innerHTML=`<div class="clinical-two-col"><div><h3>Follow-ups</h3><div>${rows.map(f=>`<article class="record-card"><strong>${escapeHtml(new Date(f.followup_datetime).toLocaleString())}</strong><span>General: ${escapeHtml(f.general_status||"—")} · Remedy: ${escapeHtml(f.remedy_response||"—")}</span><small>${escapeHtml(f.clinical_assessment||"")}</small></article>`).join("")||'<div class="empty-state">No follow-up recorded.</div>'}</div></div><form id="followup-form" class="compact-form"><h3>Record Follow-up</h3><label>Date/time<input type="datetime-local" name="followup_datetime" required></label><label>General status<select name="general_status"><option value="">—</option><option>better</option><option>same</option><option>worse</option></select></label><label>Mental status<select name="mental_status"><option value="">—</option><option>better</option><option>same</option><option>worse</option></select></label><label>Particular status<select name="particular_status"><option value="">—</option><option>better</option><option>same</option><option>worse</option></select></label><label>Remedy response<select name="remedy_response"><option value="">—</option><option>good</option><option>partial</option><option>none</option><option>aggravation</option><option>unclear</option></select></label><label>Decision<select name="decision"><option value="">—</option><option>wait</option><option>repeat</option><option>change_remedy</option><option>stop_reassess</option></select></label><label>New symptoms<textarea name="new_symptoms" rows="2"></textarea></label><label>Old symptoms<textarea name="old_symptoms" rows="2"></textarea></label><label>Clinical assessment<textarea name="clinical_assessment" rows="3"></textarea></label><label>Notes<textarea name="notes" rows="2"></textarea></label><button class="primary">Save Follow-up</button></form></div>`;
  $("#followup-form",host).addEventListener("submit",async e=>{e.preventDefault();const f=new FormData(e.currentTarget);const clean={}; for(const [k,v] of f.entries())if(v)clean[k]=k==="followup_datetime"?new Date(v).toISOString():v; try{await createFollowup({case_record_id:clinicalState.caseRecord.id,patient_id:clinicalState.patient.id,...clean});clinicalState.followups=await listFollowups(clinicalState.caseRecord.id);setStatus(host,"Follow-up saved.","success");renderFollowup(host);}catch(err){setStatus(host,err.message||"Unable to save follow-up.","error");}});
}
async function renderPrescription(host){
  if(!clinicalState.medicines.length){ try{clinicalState.medicines=await listMedicines("");}catch{clinicalState.medicines=[];} }
  $("#clinical-panel",host).innerHTML=`<div class="clinical-two-col"><div><h3>Prescription</h3>${clinicalState.prescription?`<article class="record-card"><strong>${escapeHtml(clinicalState.prescription.prescription_number)}</strong><span>${escapeHtml(clinicalState.prescription.diagnosis||"")}</span>${(clinicalState.prescription.items||[]).map(i=>`<small>${escapeHtml(i.medicine_id)} · ${escapeHtml(i.dosage)} · ${escapeHtml(i.frequency)} · Qty ${escapeHtml(i.quantity)}</small>`).join("")}</article>`:'<div class="empty-state">Select or create a prescription for this visit.</div>'}</div><form id="prescription-form" class="compact-form"><h3>Create Prescription</h3><label>Visit ID<input type="number" name="visit_id" min="1" required></label><label>Prescribed by User ID<input type="number" name="prescribed_by" min="1" required></label><label>Date/time<input type="datetime-local" name="prescription_datetime" required></label><label>Diagnosis<textarea name="diagnosis" rows="2"></textarea></label><label>Clinical notes<textarea name="clinical_notes" rows="2"></textarea></label><label>Treatment plan<textarea name="treatment_plan" rows="2"></textarea></label><div id="rx-items"></div><button type="button" id="add-rx-item">Add medicine</button><button class="primary">Create Prescription</button></form></div>`;
  const itemsHost=$("#rx-items",host); const add=()=>{const idx=itemsHost.children.length; const el=document.createElement("fieldset"); el.className="rx-item"; el.innerHTML=`<legend>Medicine ${idx+1}</legend><label>Medicine<select name="medicine_id">${clinicalState.medicines.map(m=>`<option value="${m.id}">${escapeHtml(m.medicine_name)} · ${escapeHtml(m.medicine_code)}</option>`).join("")}</select></label><label>Dosage<input name="dosage" required maxlength="100"></label><label>Frequency<input name="frequency" required maxlength="100"></label><label>Duration days<input type="number" name="duration_days" min="1"></label><label>Quantity<input type="number" name="quantity" min="0.01" step="0.01" required></label><label>Instructions<textarea name="instructions" rows="2"></textarea></label>`;itemsHost.appendChild(el);}; add(); $("#add-rx-item",host).addEventListener("click",add);
  $("#prescription-form",host).addEventListener("submit",async e=>{e.preventDefault();const f=new FormData(e.currentTarget);const itemNodes=[...itemsHost.querySelectorAll(".rx-item")];const items=itemNodes.map(n=>{const get=k=>n.querySelector(`[name=${k}]`)?.value||"";return {medicine_id:Number(get("medicine_id")),dosage:get("dosage"),frequency:get("frequency"),duration_days:get("duration_days")?Number(get("duration_days")):null,quantity:Number(get("quantity")),instructions:get("instructions")||null};});const payload={visit_id:Number(f.get("visit_id")),prescribed_by:Number(f.get("prescribed_by")),prescription_datetime:new Date(f.get("prescription_datetime")).toISOString(),diagnosis:f.get("diagnosis")||null,clinical_notes:f.get("clinical_notes")||null,treatment_plan:f.get("treatment_plan")||null,items}; try{clinicalState.prescription=await createPrescription(payload);setStatus(host,"Prescription created.","success");renderPrescription(host);}catch(err){setStatus(host,err.message||"Unable to create prescription.","error");}});
}

async function openPharmacyTab(panel, host){
  const mod=await import("./pharmacy.js");
  await mod.openPharmacyWorkspace(clinicalState.patient,panel);
}
