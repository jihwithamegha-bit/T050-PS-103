# T050-PS-103 – Advanced Verification Guide

This pack adds deeper checks beyond the existing 23 tests and the first 16 edge-case tests.

## Files
- `test_advanced_rules.py`: 14 tests for commission boundaries, TDS crossing, payout floor, reliability limits, suspension, rescheduling and duplicate weekly settlement.
- `ADVANCED_VERIFICATION_GUIDE.md`: this guide.

## Add files
Copy both files into the project root, beside `main.py`, `test_main.py` and `test_edge_cases.py`.

## Run commands
Run the tests separately first:

```powershell
python -m unittest test_advanced_rules -v
```

Then run all suites:

```powershell
python -m unittest test_main test_edge_cases test_advanced_rules -v
```

## What these tests cover
- BR-08: commission tiers at 9, 10, 24 and 25 completed sessions.
- BR-09: TDS at exactly Rs. 30,000 and when a payout crosses the threshold; payout at and below Rs. 500.
- BR-06: reliability cannot exceed 5 or fall below 0.
- BR-11: third late cancellation within 30 days triggers a 14-day suspension.
- BR-05: exactly 12 hours' notice is not a free reschedule.
- Duplicate weekly close does not create a second payout.

## Important
These tests use the current Engine API and business rules in the public project design. They change only in-memory Engine state. They do not alter `main.py`, `data/`, `docs/`, or `output/`.

A test failure is a finding to investigate, not an instruction to change the expected business rule automatically. Review the traceback and the relevant design rule before modifying application code.

## Separate manual input-failure checks
The command processor reads `data/commands.txt` and its input CSV files. To test malformed or missing files safely:
1. Make a separate copy of the entire project folder.
2. Run destructive input experiments only in that copy.
3. Keep the original `data/` directory unchanged.
4. Record whether the program exits with a clear error or silently skips/partially processes invalid input.

Suggested scenarios in the disposable copy:
- Rename `commands.txt` and run the program (missing command file).
- Make a copy of `commands.txt` containing a truncated REQUEST record.
- Add a non-numeric duration or grade in a REQUEST line.
- Remove a required column from a copied input CSV.
- Leave a required ID field blank in a copied input CSV.

Do not run these scenarios against your working project folder because the application writes generated reports to `output/`.
