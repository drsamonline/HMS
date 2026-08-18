const ALL_ACCESS_ROLES=new Set(["admin","administrator","hospital administrator","super administrator"]);
const ACCESS={
 patients:["patients.read","patient.read","patients.view","patient.view"],
 clinical:["clinical.read","case_records.read","case_record.read","clinical.case.read"],
 ipd:["ipd.read","admission.read","ipd.view"],
 investigations:["investigations.read","investigation.read","laboratory.read","xray.read"],
 billing:["billing.read","invoice.read","payments.read"],
 mrd:["mrd.read","patient_files.read","archive.read"],
 statistics:["statistics.read","statistics.view","reports.statistics"],
 reports:["reports.read","report.read","printing.read","reports.print"],
 inventory:["inventory.read","inventory.manage","stock.read","stock.manage"],
 procurement:["procurement.read","procurement.manage","purchasing.read"],
 activity:["audit.read","audit_logs.read","service_activity.read","activity.read"],
 pharmacy:["pharmacy.read","pharmacy.manage","dispensing.read","dispensing.manage"],
 administration:["departments.manage","department.manage","department_services.manage","department-services.manage"]
};
const normalize=v=>String(v??"").trim().toLowerCase();

export function canAccess(profile,module){
 if(!profile)return false;
 const roles=(profile.roles||[]).map(normalize);
 if(roles.some(r=>ALL_ACCESS_ROLES.has(r)))return true;
 const permissions=(profile.permissions||[]).map(normalize);
 if(!permissions.length)return true;
 const candidates=ACCESS[module]||[];
 return candidates.some(p=>permissions.includes(p));
}

export function applyNavigationAccess(profile){
 document.querySelectorAll(".nav-item[data-access]").forEach(button=>{
  const key=button.dataset.access;
  const allowed=canAccess(profile,key);
  button.classList.toggle("hidden",!allowed);
  button.setAttribute("aria-hidden",String(!allowed));
  button.disabled=!allowed;
 });
 const roleEl=document.querySelector("#user-role");
 if(roleEl){
  const roles=profile?.roles||[];
  roleEl.textContent=roles.length?roles.join(" · "):"Authenticated user";
 }
}

export function applyRecordAccess(profile){
 document.querySelectorAll(".record-tab[data-access]").forEach(button=>{
  const key=button.dataset.access;
  const allowed=canAccess(profile,key);
  button.classList.toggle("hidden",!allowed);
  button.disabled=!allowed;
  button.setAttribute("aria-hidden",String(!allowed));
 });
 const active=document.querySelector(".record-tab.active");
 if(active?.disabled||active?.classList.contains("hidden")){
   active.classList.remove("active");
   document.querySelector(".record-tab:not(.hidden):not([disabled])")?.classList.add("active");
 }
}

export function allowedRecordSection(profile,section){return canAccess(profile,section)}
export {ACCESS};
