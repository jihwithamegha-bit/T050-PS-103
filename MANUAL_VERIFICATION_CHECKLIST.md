# T050-PS-103 Manual Functional Verification

Run `python main.py` first, then inspect the three files under `output/`.

## Generated reports
- [ ] `match_decisions.csv` exists, opens, and contains data.
- [ ] `session_ledger.csv` exists, opens, and contains data.
- [ ] `payouts.csv` exists, opens, and contains data.
- [ ] Headers are correct and columns are separated properly.
- [ ] Currency values use two decimal places.
- [ ] No malformed rows or unexpected blank identifiers are visible.

## Match decisions
- [ ] Matched rows have a tutor ID.
- [ ] Rejected/no-match rows do not have an assigned tutor.
- [ ] Prices respect the 100.00 minimum.
- [ ] Surge flag is true/false and eligible count is non-negative.

## Session ledger
- [ ] Confirmation events are recorded.
- [ ] Student cancellation refunds match the time window.
- [ ] Tutor cancellation refunds and penalties are recorded.
- [ ] Invalid actions have explanatory notes.
- [ ] Duplicate confirmation does not confirm twice.

## Payouts
- [ ] Completed session counts are non-negative.
- [ ] Commission tier is correct.
- [ ] Penalties and TDS are in the expected columns.
- [ ] Net paid and carried-forward amounts are plausible.
- [ ] No unexpectedly negative payout values appear.

## Manual scenarios
Use a disposable copy of the project before editing `data/commands.txt`.
- [ ] Request an unavailable subject.
- [ ] Request with an unknown student ID.
- [ ] Request an unsupported duration such as 40 minutes.
- [ ] Request grade 0 and grade 13.
- [ ] Confirm the same request twice.
- [ ] Cancel an unconfirmed session.
- [ ] Complete an unconfirmed session.
- [ ] Rate the same completed session twice.
- [ ] Use a package owned by another student.
- [ ] Exhaust all package sessions.
- [ ] Create overlapping confirmed sessions for one tutor.
- [ ] Test back-to-back sessions where one ends exactly when the next begins.

## Evidence
- [ ] Screenshot of application run.
- [ ] Screenshot of original test suite.
- [ ] Screenshot of edge-case test suite.
- [ ] Screenshot of CSV verification.
- [ ] Save tracebacks for failures before changing code.

A passing test proves only the scenario it checks; it is not proof of production readiness.
