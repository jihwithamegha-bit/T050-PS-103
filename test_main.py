
import csv
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent / "output"


def load_csv(filename):
    with open(OUTPUT / filename, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


matches = load_csv("match_decisions.csv")
ledger = load_csv("session_ledger.csv")
payouts = load_csv("payouts.csv")

requests = {r["request_id"]: r for r in matches}


def check(name, condition):
    print(("PASS" if condition else "FAIL") + " - " + name)


check("80 requests processed", len(matches) == 80)
check("147 session events", len(ledger) == 147)

check(
    "Tutor ID tie-break",
    requests["REQ-001"]["tutor_id"] == "TU-005"
)

check(
    "Exactly 3 tutors: no surge",
    requests["REQ-002"]["eligible_count"] == "3"
    and requests["REQ-002"]["surge_applied"] == "false"
)

check(
    "Fewer than 3 tutors: surge",
    requests["REQ-003"]["eligible_count"] == "2"
    and requests["REQ-003"]["surge_applied"] == "true"
)

check(
    "Expired package: normal price",
    requests["REQ-008"]["price"] == "700.00"
)

check(
    "Coupon price floor",
    requests["REQ-015"]["price"] == "100.00"
)

check(
    "Invalid request not matched",
    requests["REQ-071"]["status"] == "NO_MATCH"
)

check(
    "Exactly 12h reschedule is paid",
    any(
        r["request_id"] == "REQ-004"
        and r["event"] == "RESCHEDULE"
        and r["note"].startswith("PAID_RESCHEDULE")
        for r in ledger
    )
)

check(
    "Duplicate confirmation rejected",
    any(
        r["request_id"] == "REQ-016"
        and r["note"] == "INVALID_CONFIRM"
        for r in ledger
    )
)

check(
    "Invalid rating rejected",
    any(
        r["request_id"] == "REQ-019"
        and r["note"] == "INVALID_RATING"
        for r in ledger
    )
)

check(
    "TU-010 TDS threshold",
    any(
        r["tutor_id"] == "TU-010"
        and r["week_start"] == "2026-10-12"
        and r["tds"] == "225.00"
        for r in payouts
    )
)

check(
    "Negative carryforward preserved",
    any(
        r["tutor_id"] == "TU-018"
        and r["week_start"] == "2026-10-12"
        and r["carried_forward"] == "-925.00"
        for r in payouts
    )
)

check(
    "Student no-show included in payout",
    any(
        r["tutor_id"] == "TU-022"
        and r["week_start"] == "2026-10-19"
        and r["gross"] == "2205.00"
        for r in payouts
    )
)

check(
    "TU-015 carryforward edge case",
    any(
        r["tutor_id"] == "TU-015"
        and r["carried_forward"] == "499.00"
        for r in payouts
    )
)
