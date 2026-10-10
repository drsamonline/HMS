"""Client statistics and reporting integration contracts."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
JS=ROOT/"frontend/js"
def test_stats_and_reports_modules_exist():
 assert (JS/"statistics.js").is_file()
 assert (JS/"reports.js").is_file()
def test_api_exposes_stats_and_reporting_calls():
 text=(JS/"api.js").read_text(encoding="utf-8")
 for name in ("getHospitalStatistics","getReportCatalog","buildPrintManifest","buildPrintEnvelope","buildClinicalBatch"):
  assert f"export async function {name}" in text
