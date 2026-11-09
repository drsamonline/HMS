/* The strip that says which patient you are looking at.
 *
 * Every clinical screen shows a patient, and each one rebuilt this from whatever it
 * had: some showed the name, some the number, one showed neither and relied on the
 * tab title. On a ward, the wrong-patient error is the one that matters most, so
 * the identifier is always present and always in the same place.
 */

import { escapeHtml } from "./dialog.js";

/**
 * @param {{patient_number?: string, name?: string, age?: number|string,
 *   gender?: string, phone?: string, alerts?: string[]}} patient
 */
export function patientHeader(patient) {
  const details = [
    patient.age !== undefined && patient.age !== null && patient.age !== ""
      ? `${escapeHtml(patient.age)} yrs`
      : null,
    patient.gender ? escapeHtml(patient.gender) : null,
    patient.phone ? escapeHtml(patient.phone) : null,
  ].filter(Boolean);

  const alerts = (patient.alerts || []).filter(Boolean);

  return `
    <header class="ui-patient-header">
      <div class="ui-patient-identity">
        <span class="ui-patient-number">${escapeHtml(patient.patient_number || "—")}</span>
        <strong class="ui-patient-name">${escapeHtml(patient.name || "Unnamed patient")}</strong>
        ${details.length ? `<span class="ui-patient-details">${details.join(" · ")}</span>` : ""}
      </div>
      ${
        alerts.length
          ? `<ul class="ui-patient-alerts">${alerts
              .map((alert) => `<li>${escapeHtml(alert)}</li>`)
              .join("")}</ul>`
          : ""
      }
    </header>`;
}
