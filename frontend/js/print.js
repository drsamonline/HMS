const $=(s,r=document)=>r.querySelector(s);
const esc=v=>String(v??"").replace(/[&<>'"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[c]));
const human=k=>String(k||"").replace(/_/g," ").replace(/\b\w/g,c=>c.toUpperCase());

function valueMarkup(v){
  if(v===null||v===undefined||v==="") return '<span class="print-empty">—</span>';
  if(Array.isArray(v)){
    if(!v.length) return '<span class="print-empty">No records</span>';
    return `<div class="print-list">${v.map((x,i)=>`<div class="print-list-item"><div class="print-index">${i+1}</div><div class="print-value">${valueMarkup(x)}</div></div>`).join("")}</div>`;
  }
  if(typeof v==="object"){
    const rows=Object.entries(v).map(([k,val])=>`<div class="print-field"><dt>${esc(human(k))}</dt><dd>${valueMarkup(val)}</dd></div>`).join("");
    return `<dl class="print-fields">${rows}</dl>`;
  }
  return `<span>${esc(v)}</span>`;
}

function sectionMarkup(section,label,data){
  const body=valueMarkup(data);
  return `<section class="print-section" data-print-section="${esc(section)}"><div class="print-section-heading"><h2>${esc(label)}</h2></div>${body}</section>`;
}

export function createPrintPreview(host,{manifest,envelope,title="HHMS Clinical Report",patientLabel=""}){
  host.innerHTML="";
  const sections=(manifest?.sections||[]).filter(x=>x.available!==false);
  const data=envelope?.data||{};
  const shell=document.createElement("div");
  shell.className="print-preview-shell";
  shell.innerHTML=`
    <div class="print-toolbar no-print">
      <div>
        <strong>Print Preview</strong>
        <span id="print-count" class="print-count"></span>
      </div>
      <div class="button-row">
        <button id="print-select-all" class="secondary">Select All</button>
        <button id="print-clear-all" class="secondary">Clear All</button>
        <button id="print-now">Print Selected</button>
      </div>
    </div>
    <div class="print-selector no-print"></div>
    <article class="print-document">
      <header class="print-header">
        <div class="print-brand">HHMS</div>
        <div>
          <h1>${esc(title)}</h1>
          <p>${esc(patientLabel)}</p>
          <p class="print-generated">Generated: ${esc(new Date().toLocaleString())}</p>
        </div>
      </header>
      <main id="print-pages"></main>
    </article>`;
  host.appendChild(shell);

  const selector=$(".print-selector",shell);
  const pages=$("#print-pages",shell);
  sections.forEach((sec)=>{
    const id=`print-${sec.section}`;
    const label=sec.label||human(sec.section);
    const item=document.createElement("label");
    item.className="print-select-item";
    item.innerHTML=`<input type="checkbox" value="${esc(sec.section)}" checked><span><strong>${esc(label)}</strong><small>${esc(sec.page_group||"Clinical")}</small></span>`;
    selector.appendChild(item);

    const node=document.createElement("div");
    node.dataset.section=sec.section;
    node.innerHTML=sectionMarkup(sec.section,label,data[sec.section]);
    pages.appendChild(node);
    if(sec.page_break_before) node.classList.add("print-page-break");
  });

  const selected=()=>new Set([...selector.querySelectorAll("input:checked")].map(x=>x.value));
  const apply=()=>{
    const keep=selected();
    [...pages.children].forEach(node=>{node.hidden=!keep.has(node.dataset.section)});
    $("#print-count",shell).textContent=`${keep.size} section(s) selected`;
  };
  selector.addEventListener("change",apply);
  $("#print-select-all",shell).addEventListener("click",()=>{selector.querySelectorAll("input").forEach(x=>x.checked=true);apply()});
  $("#print-clear-all",shell).addEventListener("click",()=>{selector.querySelectorAll("input").forEach(x=>x.checked=false);apply()});
  $("#print-now",shell).addEventListener("click",()=>{
    apply();
    if(!selected().size){window.alert("Select at least one section to print.");return;}
    window.print();
  });
  apply();
  return {apply, selected};
}

export function clearPrintPreview(host){ if(host) host.innerHTML=""; }
