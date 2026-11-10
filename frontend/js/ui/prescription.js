/* What a printed prescription has to carry.
 *
 * NCH Code of Ethics Regulation 7(2) requires the prescriber's registration number
 * on every prescription, and failing to display it is professional misconduct. The
 * number was stored on the practitioner since B33 and never reached the paper,
 * because the client was never sent it.
 *
 * The server now sends both name and number with every prescription. This renders
 * them, and says so plainly when the number is missing rather than printing a blank
 * line that looks like an oversight.
 */

import { escapeHtml } from "./dialog.js";

/**
 * The block that identifies who wrote the prescription.
 *
 * @param {{prescription_number?: string, prescription_datetime?: string,
 *   prescriber_name?: string|null, prescriber_registration?: string|null}} prescription
 */
export function prescriptionHeader(prescription) {
  const name = prescription.prescriber_name || "Prescriber not recorded";
  const registration = prescription.prescriber_registration
    ? `Reg. No. ${escapeHtml(prescription.prescriber_registration)}`
    : "Registration number not recorded";

  const issued = prescription.prescription_datetime
    ? `<span class="rx-issued">${escapeHtml(
        new Date(prescription.prescription_datetime).toLocaleString()
      )}</span>`
    : "";

  const missing = !prescription.prescriber_registration;

  return `
    <header class="rx-header">
      <div class="rx-identity">
        <strong class="rx-prescriber">${escapeHtml(name)}</strong>
        <span class="rx-registration${missing ? " rx-registration-missing" : ""}">${registration}</span>
      </div>
      <div class="rx-meta">
        <span class="rx-number">${escapeHtml(prescription.prescription_number || "")}</span>
        ${issued}
      </div>
    </header>`;
}
