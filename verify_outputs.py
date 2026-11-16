"""Read-only structural validation of the three generated project CSV files."""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
EXPECTED = {
    "match_decisions.csv": ["request_id", "status", "tutor_id", "score",
                            "eligible_count", "surge_applied", "price"],
    "session_ledger.csv": ["line_no", "request_id", "event", "tutor_id",
                           "amount_to_student", "refund", "penalty",
                           "reliability_after", "note"],
    "payouts.csv": ["week_start", "tutor_id", "completed_sessions", "gross",
                    "commission_pct", "commission", "penalties", "tds",
                    "carried_in", "net_paid", "carried_forward"],
}


def main():
    failures = []
    print("T050-PS-103 CSV OUTPUT VERIFICATION")
    for filename, expected_headers in EXPECTED.items():
        path = OUTPUT / filename
        print(f"\n{filename}")
        if not path.is_file():
            print("FAIL: file missing")
            failures.append(filename)
            continue
        try:
            with path.open("r", newline="", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                headers = reader.fieldnames or []
                rows = list(reader)
            if headers != expected_headers:
                print(f"FAIL: unexpected headers: {headers}")
                failures.append(filename)
            elif not rows:
                print("FAIL: no data rows")
                failures.append(filename)
            elif any(None in row for row in rows):
                print("FAIL: malformed row with extra fields")
                failures.append(filename)
            else:
                print(f"PASS: {len(rows)} rows; {len(headers)} expected columns")
                if filename == "match_decisions.csv":
                    print("Request statuses:", {
                        status: sum(r["status"] == status for r in rows)
                        for status in sorted({r["status"] for r in rows})
                    })
        except (OSError, csv.Error, UnicodeError) as exc:
            print("FAIL:", exc)
            failures.append(filename)
    print("\nRESULT:", "FAIL" if failures else "PASS")
    if failures:
        print("Review:", ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
