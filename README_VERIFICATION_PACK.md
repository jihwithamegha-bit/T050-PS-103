# T050-PS-103 Verification Pack

Copy these files into the project root beside `main.py` and `test_main.py`. Do not replace existing files.

## Included
- `test_edge_cases.py`: additional tests using the existing `main.Engine`.
- `verify_outputs.py`: read-only checks of the three generated CSV files.
- `MANUAL_VERIFICATION_CHECKLIST.md`: manual review procedure.

## Run from the project root

```powershell
python main.py
python verify_outputs.py
python -m unittest test_main test_edge_cases -v
```

The tests read the project's existing CSV data. The CSV checker reads generated reports. Neither script modifies `data/`, `main.py`, `test_main.py`, or output reports.
