/* A trend line small enough to sit in a card.
 *
 * Drawn as inline SVG rather than pulled from a charting library: one line per
 * indicator does not justify a dependency in a product that ships to hospitals over
 * a LAN and has to keep working when the internet does not.
 *
 * The rule that matters: a month with no data is a gap, not a zero. Plotting a
 * missing month as zero draws a plunge that never happened, and the person reading
 * it has no way to tell.
 */

/**
 * @param {Array<{value: number|null, available: boolean}>} points
 * @param {{width?: number, height?: number}} options
 * @returns {string} an <svg> element, or an empty-state line
 */
export function sparkline(points, options = {}) {
  const width = options.width || 120;
  const height = options.height || 28;
  const known = points.filter((point) => point.available && point.value !== null);

  if (known.length < 2) {
    return `<span class="spark-empty">not enough months to show a trend</span>`;
  }

  const values = known.map((point) => point.value);
  const max = Math.max(...values);
  const min = Math.min(...values);
  // A flat series would divide by zero; give it a band so it draws mid-height.
  const span = max - min || Math.abs(max) || 1;

  const step = width / Math.max(points.length - 1, 1);
  const coords = points.map((point, index) => {
    if (!point.available || point.value === null) return null;
    const x = index * step;
    const y = height - ((point.value - min) / span) * (height - 4) - 2;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  // Break the path at every gap rather than joining across it.
  const segments = [];
  let current = [];
  coords.forEach((coord) => {
    if (coord === null) {
      if (current.length) segments.push(current);
      current = [];
    } else {
      current.push(coord);
    }
  });
  if (current.length) segments.push(current);

  const paths = segments
    .filter((segment) => segment.length > 1)
    .map(
      (segment) =>
        `<polyline points="${segment.join(" ")}" fill="none" stroke="var(--border-focus)" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>`
    )
    .join("");

  if (!paths) {
    return `<span class="spark-empty">not enough months to show a trend</span>`;
  }

  return `<svg class="spark" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-label="Trend over the last ${points.length} months">${paths}</svg>`;
}
