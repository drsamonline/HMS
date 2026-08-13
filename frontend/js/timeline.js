import{listVisits,listAdmissions,listInvestigations,listInvoices,listPatientFiles}from"./api.js";
const esc=v=>String(v??"").replace(/[&<>'"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[c]));
const fmt=v=>{if(!v)return"—";const d=new Date(v);return Number.isNaN(d.getTime())?String(v):d.toLocaleString()};
const status=(el,msg,kind="")=>{el.textContent=msg;el.className=`status-box ${kind}`.trim()};
const item=(date,type,title,meta,detail="")=>({date:new Date(date||0),type,title,meta,detail});
export async function openPatientTimeline(box,patient){
 box.innerHTML=`<div class="module-head"><div><h3>Patient Timeline</h3><p>Longitudinal view of the patient's recorded hospital activity.</p></div><button id="timeline-refresh" class="secondary">Refresh</button></div><div id="timeline-status" class="status-box"></div><div id="timeline-summary" class="timeline-summary"></div><div id="timeline-list" class="timeline-list"></div>`;
 const st=box.querySelector("#timeline-status"), list=box.querySelector("#timeline-list"), summary=box.querySelector("#timeline-summary");
 const load=async()=>{
  try{
   status(st,"Loading patient timeline…");
   const [visits,admissions,investigations,invoices,files]=await Promise.all([
    listVisits(patient.id),listAdmissions(patient.id),listInvestigations(patient.id),listInvoices(patient.id),listPatientFiles(patient.id)
   ]);
   const events=[
    ...(visits||[]).map(v=>item(v.visit_datetime,"OPD Visit",v.visit_number||"OPD Visit",`${v.visit_type||"OPD"} · ${v.consultation_status||"—"}`,v.chief_complaint||"")),
    ...(admissions||[]).map(a=>item(a.admission_datetime,"IPD Admission",a.admission_number||"Admission",`${a.admission_status||"—"} · Bed ${a.bed_id||"—"}`,a.admission_reason||"")),
    ...(investigations||[]).map(x=>item(x.requested_datetime||x.investigation_datetime,"Investigation",x.investigation_name||x.test_name||"Investigation",`${x.investigation_status||"—"} · ${x.fulfillment_mode||"—"}`,x.remarks||"")),
    ...(invoices||[]).map(i=>item(i.invoice_date,"Billing",i.invoice_number||"Invoice",`${i.status||"—"} · Total ${i.total_amount??"—"}`,i.notes||"")),
    ...(files||[]).map(f=>item(f.created_at,"MRD",f.file_no||"Patient File",`${f.file_type||"—"} · ${f.status||"—"}`,f.location||""))
   ].sort((a,b)=>b.date-a.date);
   summary.innerHTML=`<div class="timeline-stat"><strong>${events.length}</strong><span>Timeline events</span></div><div class="timeline-stat"><strong>${visits?.length||0}</strong><span>OPD visits</span></div><div class="timeline-stat"><strong>${admissions?.length||0}</strong><span>Admissions</span></div><div class="timeline-stat"><strong>${investigations?.length||0}</strong><span>Investigations</span></div>`;
   list.innerHTML=events.length?events.map(e=>`<article class="timeline-item"><div class="timeline-dot"></div><div class="timeline-card"><div class="timeline-top"><span class="timeline-type">${esc(e.type)}</span><time>${esc(fmt(e.date))}</time></div><h4>${esc(e.title)}</h4><p class="timeline-meta">${esc(e.meta)}</p>${e.detail?`<p>${esc(e.detail)}</p>`:""}</div></article>`).join(""):'<div class="empty-state">No clinical or administrative activity has been recorded for this patient yet.</div>';
   status(st,"Timeline loaded.","success");
  }catch(e){status(st,e?.message||"Unable to load patient timeline.","error");list.innerHTML=""}
 };
 box.querySelector("#timeline-refresh").addEventListener("click",load);await load();
}
