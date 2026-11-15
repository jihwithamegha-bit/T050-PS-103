# PS-103 — Online Tutoring Marketplace
## Session Matching, Cancellation and Tutor Payout Engine

**Team ID:** T050  
**Organization:** 10 SECONDS  
**Domain:** EdTech — Online Tutoring Marketplace  
**Programming Language:** Python 3.10+

## 1. Project Overview

This project implements a command-file-driven backend engine for an online tutoring marketplace. It automates tutor matching, session booking, pricing, cancellations, rescheduling, tutor performance tracking, and weekly payout calculations.

The system processes predefined input files and generates CSV reports. A graphical user interface is not required.

## 2. Project Objectives

- Match students with suitable tutors based on subject, grade, language and availability.
- Rank eligible tutors using a deterministic scoring formula.
- Calculate session fees, surge pricing, package discounts and coupons.
- Process booking confirmations, cancellations, rescheduling and no-shows.
- Track tutor reliability, ratings and matching suspensions.
- Calculate weekly commission, penalties, tax deductions and tutor payouts.
- Generate reports for matching decisions, session events and payouts.

## 3. Technologies Used

- Python 3.10+
- Python standard library
- CSV files for input and output
- `unittest` for automated testing
- Visual Studio Code for development
- GitHub for version control and submission

## 4. Project Structure

```text
T050-PS-103/
├── data/
│   ├── README.md
│   ├── tutors.csv
│   ├── students.csv
│   ├── availability.csv
│   ├── rating_history.csv
│   ├── packages.csv
│   └── commands.txt
├── docs/
│   ├── design.md
│   ├── design.pdf
│   └── WEEK3_VALIDATION_NOTES.md
├── output/
│   ├── match_decisions.csv
│   ├── session_ledger.csv
│   └── payouts.csv
├── main.py
├── test_main.py
├── .gitignore
└── README.md
```

## 5. Business Rules

The engine is designed around 12 business rules.

| Rule | Description |
|---|---|
| BR-01 | Tutor eligibility based on subject, grade, language, availability and session duration |
| BR-02 | Deterministic tutor ranking with tie-breaking rules |
| BR-03 | Surge pricing for qualifying weekday evening sessions |
| BR-04 | Session package discounts, validity and tutor restrictions |
| BR-05 | Student cancellations, refunds and rescheduling |
| BR-06 | Tutor cancellations, reliability penalties and coupons |
| BR-07 | Student and tutor no-show handling |
| BR-08 | Weekly tiered platform commission |
| BR-09 | Weekly tutor payouts, TDS and carryforward |
| BR-10 | Tutor rating averages and demotion rules |
| BR-11 | Temporary suspension after repeated late tutor cancellations |
| BR-12 | Pricing precedence, coupon application and minimum session price |

Detailed rule definitions are maintained in the project design documentation.

## 6. Input Files

The program reads tutor profiles, student information, availability schedules, rating history, package details and chronological commands from the `data/` directory.

The `commands.txt` file contains events such as session requests, confirmations, cancellations, rescheduling, no-shows, ratings and week closures.

The input data formats are documented in `data/README.md`.

## 7. How to Run the Project

### Prerequisites

Install Python 3.10 or later.

### Execution

Open the project folder in Visual Studio Code and open the integrated terminal.

Run:

```bash
python main.py
```

The program processes the input data and generates CSV reports inside the `output/` directory.

## 8. Generated Output Files

| File | Purpose |
|---|---|
| `match_decisions.csv` | Records tutor matching and selection decisions |
| `session_ledger.csv` | Records session events, pricing and related transactions |
| `payouts.csv` | Records weekly tutor payout calculations |

## 9. Automated Testing

The project includes automated unit tests covering the 12 business-rule areas and selected edge cases.

To execute the test suite, run:

```bash
python -m unittest test_main -v
```

**Latest recorded local test result:** 23 tests executed successfully, with no failures.

Passing these tests confirms the checked scenarios but does not guarantee success on every unseen evaluation case.

## 10. Validation and Edge Cases

The project includes tests or validation checks for scenarios involving:

- Tutor ranking and tie-breaking
- Surge pricing eligibility
- Rescheduling time boundaries
- TDS threshold crossing
- Package expiration
- Tutor rating thresholds
- Minimum payout carryforward
- Coupon application and minimum pricing

Further validation may be required for combinations of rules and evaluator-provided hidden cases.

See `docs/WEEK3_VALIDATION_NOTES.md` for recorded validation results and known discrepancies.

## 11. Design Approach

The system uses deterministic rule-based processing.

Commands are processed in their supplied order, and decisions are calculated using defined eligibility, ranking, pricing and payout policies.

The program is organized around input processing, business-rule evaluation, session state management and output generation.

## 12. Known Limitations

- The application is command-file-driven and does not include a graphical interface.
- The provided sample data contains a documented tutor-selection discrepancy involving TU-015 and TU-009.
- Passing the current automated tests does not establish complete correctness for hidden evaluation inputs.
- Final validation and documentation updates remain part of the Week 4 completion process.

## 13. Future Enhancements

Possible future improvements include:

- A web-based student and tutor interface
- Database integration
- Online booking and payment services
- Real-time tutor availability updates
- Administrative dashboards

These are potential extensions, not requirements for the current command-file-driven implementation.

## 14. Conclusion

The Online Tutoring Marketplace Engine demonstrates how deterministic business rules can automate tutor selection, session management, pricing and weekly financial settlement.

It provides a foundation for building a larger online tutoring platform while keeping matching and payment decisions transparent and testable.

---

**Team:** T050  
**Problem Statement:** PS-103  
**Capstone Program:** 10 SECONDS
