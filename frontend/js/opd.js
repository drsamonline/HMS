import { listPatients, createVisit, listOPDTokens, createOPDToken, updateOPDToken, cancelOPDToken } from "./api.js";
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[c]));
const today = () => new Date().toISOString().slice(0, 10);
const patientName = (p) => [p.first_name, p.middle_name, p.last_name].filter(Boolean).join(" ") || p.patient_number || `Patient ${p.id}`;
export async function openOPDQueueWorkspace(box){
  box.innerHTML = `<div class="module-workspace">
    <div class="module-head"><div><h2>OPD Queue</h2><p>Register visits, generate tokens and manage the outpatient queue.</p></div><button id="opd-refresh" class="secondary">Refresh</button></div>
    <div class="opd-toolbar"><label>Date<input id="opd-date" type="date" value="${today()}"></label><label>Patient search<input id="opd-patient-search" type="search" placeholder="Patient number, name or mobile"></label><button id="opd-find">Find patient</button></div>
    <div id="opd-results"></div><div id="opd-selected" class="status-box hidden"></div>
    <form id="opd-form" class="compact-form hidden"><h3>Register OPD Visit</h3><input name="patient_id" type="hidden"><label>Visit type<select name="visit_type"><option value="opd">OPD</option><option value="followup">Follow-up</option></select></label><label>Case type<select name="case_type"><option value="new">New</option><option value="old">Old</option></select></label><label>Chief complaint<textarea name="chief_complaint" rows="3"></textarea></label><div class="button-row"><button type="submit">Create Visit & Token</button><button id="opd-cancel" type="button" class="secondary">Cancel</button></div></form>
    <div id="opd-status" class="status-box"></div><div id="opd-queue" class="table-wrap"></div></div>`;
  const date = box.querySelector("#opd-date"), search = box.querySelector("#opd-patient-search"), results = box.querySelector("#opd-results"), selected = box.querySelector("#opd-selected"), form = box.querySelector("#opd-form"), status = box.querySelector("#opd-status"), queue = box.querySelector("#opd-queue");
  let patient = null;
  const show = (m, k="") => { status.textContent=m; status.className=`status-box ${k}`.trim(); };
  async function find(){
    if(!search.value.trim()){results.replaceChildren();return;}
    try{
      const rows=await listPatients(search.value.trim());
      results.innerHTML=rows.length?rows.slice(0,8).map(p=>`<button type="button" class="patient-card" data-id="${p.id}"><strong>${esc(patientName(p))}</strong><span>${esc(p.patient_number)} · ${esc(p.gender||"—")} · ${esc(p.mobile_number||"—")}</span></button>`).join(""):"<div class=\"empty-state\">No patients found.</div>";
      results.querySelectorAll("[data-id]").forEach(b=>b.onclick=()=>{patient=rows.find(p=>String(p.id)===b.dataset.id);form.elements.patient_id.value=patient.id;selected.textContent=`Selected: ${patientName(patient)} (${patient.patient_number})`;selected.classList.remove("hidden");form.classList.remove("hidden");results.replaceChildren();});
    }catch(e){show(e.message||"Unable to search patients.","error")}
  }
  async function refresh(){
    try{
      const rows=await listOPDTokens(date.value);
      queue.innerHTML=rows.length?`<table><thead><tr><th>Token</th><th>Visit</th><th>Status</th><th>Generated</th><th>Actions</th></tr></thead><tbody>${rows.map(t=>`<tr><td><strong>${t.token_number}</strong></td><td>${t.visit_id}</td><td>${esc(t.queue_status)}</td><td>${esc(new Date(t.generated_at).toLocaleTimeString())}</td><td class="opd-actions"><button data-a="call" data-id="${t.id}" ${t.queue_status!=="waiting"?"disabled":""}>Call</button><button data-a="complete" data-id="${t.id}" ${t.queue_status!=="in_consultation"?"disabled":""}>Complete</button><button class="secondary" data-a="cancel" data-id="${t.id}" ${["completed","cancelled"].includes(t.queue_status)?"disabled":""}>Cancel</button></td></tr>`).join("")}</tbody></table>`:"<div class=\"empty-state\">No OPD tokens for this date.</div>";
      queue.querySelectorAll("[data-a]").forEach(b=>b.onclick=async()=>{try{if(b.dataset.a==="call")await updateOPDToken(b.dataset.id,{queue_status:"in_consultation"});else if(b.dataset.a==="complete")await updateOPDToken(b.dataset.id,{queue_status:"completed"});else await cancelOPDToken(b.dataset.id);await refresh();}catch(e){show(e.message||"Unable to update token.","error")}});
      show(`${rows.length} token(s) loaded.`,"success");
    }catch(e){show(e.message||"Unable to load OPD queue.","error")}
  }
  box.querySelector("#opd-find").onclick=find; search.addEventListener("keydown",e=>{if(e.key==="Enter"){e.preventDefault();find()}}); box.querySelector("#opd-refresh").onclick=refresh; date.onchange=refresh;
  box.querySelector("#opd-cancel").onclick=()=>{patient=null;selected.classList.add("hidden");form.classList.add("hidden");form.reset()};
  form.onsubmit=async e=>{e.preventDefault();if(!patient)return;try{show("Creating visit and token…");const fd=new FormData(form);const userId=Number(window.hhmsCurrentUserId||0);if(!userId)throw new Error("Authenticated doctor ID is unavailable.");const visit=await createVisit({patient_id:Number(fd.get("patient_id")),visit_type:fd.get("visit_type"),visit_datetime:new Date().toISOString(),chief_complaint:fd.get("chief_complaint")||null,consultation_status:"registered",consulting_doctor_id:userId,case_type:fd.get("case_type")});await createOPDToken({visit_id:visit.id,queue_date:date.value});show("Visit registered and OPD token generated.","success");const patientId=Number(fd.get("patient_id"));patient=null;selected.classList.add("hidden");form.classList.add("hidden");form.reset();await refresh();window.dispatchEvent(new CustomEvent("hhms:open-patient-clinical",{detail:{patientId}}));}catch(e){show(e.message||"Unable to create visit/token.","error")}};
  await refresh();
}
