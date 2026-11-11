/* A prescription as a document, previewed before it prints.
 *
 * Every other record in HHMS prints. The prescription - the one document a patient
 * physically leaves with - did not, so the registration number added in B31 was
 * visible on screen and nowhere else.
 *
 * The preview is the document: the same markup is what window.print() sends, so
 * what is checked on screen is what comes out. A separate print path is how the
 * two drift.
 */

import { escapeHtml } from "./dialog.js";
import { patientHeader } from "./patient-header.js";
import { prescriptionHeader } from "./prescription.js";
import { notify } from "./dialog.js";

function itemsTable(items) {
  if (!items || !items.length) {
    return `<p class="print-empty">No medicines were prescribed.</p>`;
  }
  const rows = items
    .map(
      (item, index) => `
      <tr>
        <td>${index + 1}</td>
        <td>${escapeHtml(item.medicine_name ?? item.medicine_id ?? "")}</td>
        <td>${escapeHtml(item.dosage ?? "")}</td>
        <td>${escapeHtml(item.frequency ?? "")}</td>
        <td>${escapeHtml(item.duration_days ?? "")}</td>
        <td>${escapeHtml(item.quantity ?? "")}</td>
        <td>${escapeHtml(item.instructions ?? "")}</td>
      </tr>`
    )
    .join("");

  return `
    <table class="rx-items-table">
      <thead>
        <tr>
          <th>#</th><th>Medicine</th><th>Dosage</th><th>Frequency</th>
          <th>Days</th><th>Qty</th><th>Instructions</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

/**
 * Render the prescription as a printable document into a host element.
 *
 * @param {HTMLElement} host
 * @param {{prescription: Object, patient: Object, hospitalName?: string}} spec
 */
export function createPrescriptionPrintPreview(host, spec) {
  const { prescription, patient } = spec;
  host.innerHTML = "";

  const shell = document.createElement("div");
  shell.className = "print-preview-shell";
  shell.innerHTML = `
    <div class="print-toolbar no-print">
      <div><strong>Prescription Preview</strong><span class="print-count">Check it before it is signed.</span></div>
      <div class="button-row">
        <button id="rx-print-close" class="secondary">Close</button>
        <button id="rx-print-now">Print</button>
      </div>
    </div>
    <article class="print-document rx-document">
      <header class="print-header">
        <div class="print-brand">HHMS</div>
        <div>
          <h1>${escapeHtml(spec.hospitalName || "Prescription")}</h1>
          <p class="print-generated">Generated: ${escapeHtml(new Date().toLocaleString())}</p>
        </div>
      </header>
      ${patientHeader(patient || {})}
      ${prescriptionHeader(prescription || {})}
      <section class="print-section" data-print-section="items">
        <div class="print-section-heading"><h2>Medicines</h2></div>
        ${itemsTable(prescription?.items)}
      </section>
      ${
        prescription?.diagnosis
          ? `<section class="print-section" data-print-section="diagnosis">
               <div class="print-section-heading"><h2>Diagnosis</h2></div>
               <p>${escapeHtml(prescription.diagnosis)}</p>
             </section>`
          : ""
      }
      ${
        prescription?.treatment_plan
          ? `<section class="print-section" data-print-section="plan">
               <div class="print-section-heading"><h2>Treatment plan</h2></div>
               <p>${escapeHtml(prescription.treatment_plan)}</p>
             </section>`
          : ""
      }
      <footer class="rx-footer">
        <p>This prescription is valid only with the prescriber's registration number shown above.</p>
      </footer>
    </article>`;

  host.appendChild(shell);

  shell.querySelector("#rx-print-close").addEventListener("click", () => {
    host.innerHTML = "";
  });
  shell.querySelector("#rx-print-now").addEventListener("click", () => {
    if (!prescription?.items?.length) {
      notify("There is nothing to print: no medicines were prescribed.", "warning");
      return;
    }
    window.print();
  });

  return shell;
}
