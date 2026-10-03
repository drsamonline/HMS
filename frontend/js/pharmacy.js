
import {
  getAccessToken,
  listMedicines,
  getMedicineStock,
  getDispensesForPrescriptionItem,
  createDispense,
  getCurrentUserProfile,
} from "./api.js";

let state = { patient: null, medicines: [], stock: [], userId: null };

const esc=v=>String(v??"").replace(/[&<>'"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));
const status=(h,m,k="")=>{const e=h.querySelector("[data-pharmacy-status]");if(e){e.textContent=m;e.className=`status-box ${k}`.trim()}};

export function initPharmacyWorkspace(){ window.hhmsPharmacy = { open: openPharmacyWorkspace }; }

export async function openPharmacyWorkspace(patient,host){
  state={patient,medicines:[],stock:[],userId:null};
  host.innerHTML=`<section class="module-workspace pharmacy-workspace">
    <div class="module-header"><div><h3>Pharmacy / Dispensing</h3><p>Search medicines, inspect available batches, and dispense against prescription items.</p></div><button type="button" class="secondary" data-ph-refresh>Refresh</button></div>
    <div class="status-box" data-pharmacy-status>Loading prescriptions…</div>
    <div class="pharmacy-grid">
      <section class="content-panel"><h4>Patient prescriptions</h4><div data-ph-prescriptions class="record-card-list"></div></section>
      <section class="content-panel"><h4>Selected prescription item</h4><div data-ph-item><div class="empty-state">Select a prescription item.</div></div></section>
    </div>
  </section>`;
  host.querySelector("[data-ph-refresh]").addEventListener("click",()=>load(host));
  await load(host);
}

async function load(host){
  if(!state.patient){status(host,"No patient selected.","error");return}
  try{
    const [profile]=await Promise.all([getCurrentUserProfile(), import("./clinical.js").then(()=>null)]);
    state.userId=profile?.user?.id||profile?.id||null;
    const {listVisits,getPrescription}=await import("./api.js");
    const visits=await listVisits(state.patient.id);
    const cards=[];
    for(const visit of visits.slice(0,20)){
      try{
        const rx=await getPrescriptionForVisit(getPrescription,visit.id);
        if(rx) cards.push(renderPrescriptionCard(rx,visit,host));
      }catch{}
    }
    const list=host.querySelector("[data-ph-prescriptions]");
    list.replaceChildren(...cards);
    status(host,cards.length?`${cards.length} prescription(s) available for dispensing.`:"No prescriptions available for this patient.","");
  }catch(e){status(host,e.message,"error")}
}

async function getPrescriptionForVisit(getPrescriptionFn,visitId){
  // Existing API may expose list-by-visit; use it when present.
  const mod=await import("./api.js");
  if(typeof mod.listPrescriptions==="function"){
    const rows=await mod.listPrescriptions(visitId);
    return Array.isArray(rows)?rows.at(-1)||null:rows;
  }
  return null;
}

function renderPrescriptionCard(rx,visit,host){
  const el=document.createElement("article");el.className="record-card";
  el.innerHTML=`<strong>${esc(rx.prescription_number||`Prescription #${rx.id}`)}</strong>
    <span>${esc(rx.prescription_datetime||visit.visit_datetime||"—")}</span>
    <div class="record-card-list pharmacy-item-list">
      ${(rx.items||[]).map(item=>`<button type="button" class="record-card pharmacy-item" data-item-id="${item.id}" data-medicine-id="${item.medicine_id}">
        <strong>Medicine #${esc(item.medicine_id)}</strong><span>${esc(item.dosage)} · ${esc(item.frequency)} · Qty ${esc(item.quantity)}</span>
      </button>`).join("")}
    </div>`;
  el.querySelectorAll("[data-item-id]").forEach(b=>b.addEventListener("click",()=>selectItem(rx,b.dataset.itemId,host)));
  return el;
}

async function selectItem(rx,itemId,host){
  const item=(rx.items||[]).find(x=>String(x.id)===String(itemId)); if(!item)return;
  try{
    const med=state.medicines.find(x=>String(x.id)===String(item.medicine_id))||((await listMedicines("")).find(x=>String(x.id)===String(item.medicine_id)));
    if(med && !state.medicines.some(x=>x.id===med.id)) state.medicines.push(med);
    const stock=await getMedicineStock(item.medicine_id);
    state.stock=stock;
    const dispensed=await getDispensesForPrescriptionItem(item.id);
    const total=dispensed.reduce((s,x)=>s+Number(x.quantity_dispensed||0),0);
    const requested=Number(item.quantity||0);
    const remaining=Math.max(0,requested-total);
    const panel=host.querySelector("[data-ph-item]");
    panel.innerHTML=`<div class="clinical-detail">
      <h4>${esc(med?.medicine_name||`Medicine #${item.medicine_id}`)}</h4>
      <p>Prescribed: ${esc(item.quantity)} · Already dispensed: ${total} · Remaining: ${remaining}</p>
      <label>Stock batch<select data-ph-stock ${remaining>0?"":"disabled"}>${stock.map(b=>`<option value="${b.id}" data-remaining="${esc(b.quantity_remaining)}">${esc(b.batch_no)} · Available ${esc(b.quantity_remaining)}${b.expiry_date?` · Exp ${esc(b.expiry_date)}`:""}</option>`).join("")}</select></label>
      <label>Dispense quantity<input data-ph-qty type="number" min="0.01" step="0.01" value="${remaining}" ${remaining>0?"":"disabled"}></label>
      <label>Notes<textarea data-ph-notes rows="2"></textarea></label>
      <button type="button" data-ph-save ${remaining>0 && stock.length && state.userId?"":"disabled"}>Record Dispense</button>
      <div data-ph-item-status class="status-box"></div>
    </div>`;
    panel.querySelector("[data-ph-save]")?.addEventListener("click",()=>saveDispense(rx,item,host));
  }catch(e){status(host,e.message,"error")}
}

async function saveDispense(rx,item,host){
  const panel=host.querySelector("[data-ph-item]"); const sel=panel.querySelector("[data-ph-stock]"); const qty=Number(panel.querySelector("[data-ph-qty]").value||0); const notes=panel.querySelector("[data-ph-notes]").value.trim();
  const batch=state.stock.find(x=>String(x.id)===String(sel?.value));
  if(!batch||qty<=0){panel.querySelector("[data-ph-item-status]").textContent="Select a stock batch and enter a valid quantity.";return}
  if(qty>Number(batch.quantity_remaining||0)){panel.querySelector("[data-ph-item-status]").textContent="Dispense quantity exceeds available stock.";return}
  try{
    await createDispense({prescription_item_id:item.id,medicine_id:item.medicine_id,stock_batch_id:batch.id,quantity_dispensed:qty,dispensed_by:state.userId,notes:notes||null});
    panel.querySelector("[data-ph-item-status]").textContent="Dispense recorded successfully.";
    panel.querySelector("[data-ph-item-status]").className="status-box success";
    await selectItem(rx,item.id,host);
  }catch(e){panel.querySelector("[data-ph-item-status]").textContent=e.message;panel.querySelector("[data-ph-item-status]").className="status-box error"}
}
