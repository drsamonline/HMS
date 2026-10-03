import { getOperationalYear, updateOperationalYear } from './api.js';

export async function renderOperationalYearSettings(host) {
  host.innerHTML = `
    <section class="content-card">
      <header class="workspace-header">
        <div><h2>Operational Year</h2><p>Configure calendar-year or financial-year operation.</p></div>
      </header>
      <form id="operational-year-form" class="compact-form">
        <label>Basis
          <select name="basis">
            <option value="calendar">Calendar Year (1 Jan – 31 Dec)</option>
            <option value="financial">Financial Year</option>
          </select>
        </label>
        <div id="financial-start" class="structured-row">
          <label>Financial year start month
            <select name="start_month">
              ${Array.from({length:12},(_,i)=>`<option value="${i+1}">${new Date(2000,i,1).toLocaleString(undefined,{month:'long'})}</option>`).join('')}
            </select>
          </label>
          <label>Start day<input name="start_day" type="number" min="1" max="31" value="1"></label>
        </div>
        <div id="operational-year-status" class="status-box"></div>
        <button class="primary" type="submit">Save Operational Year</button>
      </form>
    </section>`;
  const form=host.querySelector('#operational-year-form');
  const start=host.querySelector('#financial-start');
  const status=host.querySelector('#operational-year-status');
  const toggle=()=>{start.style.display=form.basis.value==='financial'?'grid':'none';};
  form.basis.addEventListener('change',toggle);
  const current=await getOperationalYear();
  form.basis.value=current.basis; form.start_month.value=String(current.start_month); form.start_day.value=String(current.start_day); toggle();
  status.textContent=`Current operational year: ${current.label}`;
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    try{const saved=await updateOperationalYear({basis:form.basis.value,start_month:Number(form.start_month.value),start_day:Number(form.start_day.value)}); status.textContent=`Saved. Current operational year: ${saved.label}`; status.className='status-box success';}
    catch(err){status.textContent=err.message||'Unable to save operational year.'; status.className='status-box error';}
  });
}
