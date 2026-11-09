/* One worklist table, used by every list screen.
 *
 * The screens each built their own: some had a header row, some did not; some
 * escaped their cells, some did not; sorting existed in two places and in two
 * different directions. This is the one the rest of the interface uses.
 */

import { escapeHtml } from "./dialog.js";
import { emptyState, noResultsState } from "./states.js";

/**
 * Render a table.
 *
 * @param {{columns: Array<{key: string, label: string, align?: string,
 *   render?: Function}>, rows: Array<Object>, rowKey?: string,
 *   onRowClick?: Function, emptyTitle?: string, emptyMessage?: string,
 *   actionLabel?: string, actionId?: string, query?: string}} spec
 */
export function dataTable(spec) {
  const { columns, rows } = spec;

  if (!rows.length) {
    return spec.query
      ? noResultsState({ query: spec.query })
      : emptyState({
          title: spec.emptyTitle,
          message: spec.emptyMessage,
          actionLabel: spec.actionLabel,
          actionId: spec.actionId,
        });
  }

  const head = columns
    .map(
      (column) =>
        `<th scope="col"${column.align ? ` class="align-${escapeHtml(column.align)}"` : ""}>${escapeHtml(
          column.label
        )}</th>`
    )
    .join("");

  const body = rows
    .map((row) => {
      const cells = columns
        .map((column) => {
          // A render function is trusted with its own escaping; a plain value is not.
          const value = column.render ? column.render(row) : escapeHtml(row[column.key] ?? "");
          return `<td${column.align ? ` class="align-${escapeHtml(column.align)}"` : ""}>${value}</td>`;
        })
        .join("");
      const key = spec.rowKey ? ` data-row-key="${escapeHtml(row[spec.rowKey])}"` : "";
      return `<tr${key}>${cells}</tr>`;
    })
    .join("");

  return `
    <table class="ui-table">
      <thead><tr>${head}</tr></thead>
      <tbody>${body}</tbody>
    </table>`;
}

/** Attach click handling to a table rendered by dataTable. */
export function bindRowClicks(host, onRowClick) {
  if (!onRowClick) return;
  host.querySelectorAll("tbody tr[data-row-key]").forEach((row) => {
    row.addEventListener("click", () => onRowClick(row.dataset.rowKey, row));
  });
}
