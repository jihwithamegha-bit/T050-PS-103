# Decision Log — PS-103 Online Tutoring Marketplace

**Team:** T050  
**Organization:** 10 SECONDS  
**Project:** Session Matching, Cancellation and Tutor Payout Engine  
**Language:** Python 3.10+

## 1. Purpose

This decision log documents the major design choices, implementation decisions, assumptions, and trade-offs made during development of the Online Tutoring Marketplace Engine.

The objective is to make the system's behavior understandable, reproducible, and easier to evaluate.

## 2. Architecture Decisions

### D01 — Python as the Implementation Language

**Decision:** Use Python 3.10+.

**Reason:** Python supports readable business-rule implementation, CSV processing, date calculations, and automated testing.

**Trade-off:** The solution is a command-line application rather than a graphical interface.

### D02 — Command-File-Driven Processing

**Decision:** Process events from `data/commands.txt` in their supplied order.

**Reason:** The assignment requires chronological command processing and reproducible results.

**Trade-off:** The system processes predefined commands instead of receiving live user requests.

### D03 — CSV-Based Input and Output

**Decision:** Use CSV files for tutor information, students, availability, packages, ratings, and generated reports.

**Reason:** CSV files are simple, portable, and compatible with the supplied dataset.

**Trade-off:** A database would be more suitable for a large production marketplace.

### D04 — Deterministic Tutor Matching

**Decision:** Apply the official eligibility requirements and ranking formula.

**Formula:**

`Score = Rating × 10 + Reliability × 5 − (Tutor Rate − Minimum Eligible Rate) / 100`

**Tie-breaking order:**

1. Higher score.
2. Fewer confirmed sessions during the week.
3. Lower tutor ID.

**Reason:** Identical inputs should produce consistent matching decisions.

### D05 — Session Pricing

**Decision:** Calculate the session base price using the tutor's hourly rate and session duration.

`Base Price = Hourly Rate × Duration / 60`

Apply applicable surge pricing, package discounts, and coupons according to the business rules.

**Reason:** A fixed calculation order supports consistent pricing and easier testing.

### D06 — Cancellation and Rescheduling

**Decision:** Apply cancellation and refund rules based on the exact time remaining before the scheduled session.

**Reason:** Time boundaries determine the correct refund, penalty, and rescheduling outcome.

**Important boundaries:** 6 hours, 12 hours, and 24 hours.

### D07 — Tutor Reliability and Ratings

**Decision:** Maintain tutor reliability and rating information separately.

**Reason:** Reliability reflects attendance and cancellation behavior, while ratings represent student feedback.

Both affect tutor matching eligibility or ranking.

### D08 — Weekly Commission

**Decision:** Determine the platform commission tier using the tutor's completed session count for the week.

**Commission tiers:**

| Weekly completed sessions | Commission |
|---|---|
| Fewer than 10 | 25% |
| 10–24 | 20% |
| 25 or more | 15% |

**Reason:** The commission tier depends on total weekly performance.

### D09 — Tutor Payout and TDS

**Decision:** Calculate tutor payouts after accounting for applicable commission, penalties, tax deductions, and carried balances.

**Rules:**

- Weekly payouts are scheduled for Wednesday.
- A 10% TDS deduction applies according to the specified annual threshold rule.
- Balances below ₹500 are carried forward.

**Reason:** The payout engine must account for both session earnings and financial adjustments.

### D10 — Automated Testing

**Decision:** Use Python's built-in `unittest` framework.

**Reason:** Automated tests allow repeatable checks of the business rules without requiring additional third-party packages.

**Latest recorded result:** 23 tests passed.

**Limitation:** Passing the current tests does not guarantee correctness on every hidden evaluation input.

## 3. Business-Rule Coverage

| Business rule | Main responsibility |
|---|---|
| BR-01 | Tutor eligibility |
| BR-02 | Tutor ranking |
| BR-03 | Surge pricing |
| BR-04 | Packages |
| BR-05 | Student cancellation and rescheduling |
| BR-06 | Tutor cancellation and penalties |
| BR-07 | No-shows |
| BR-08 | Weekly commission |
| BR-09 | Payouts and TDS |
| BR-10 | Ratings and demotion |
| BR-11 | Tutor suspension |
| BR-12 | Pricing precedence and minimum price |

## 4. Assumptions

1. Input timestamps use the formats specified in the supplied dataset documentation.
2. Commands are processed in file order.
3. Session durations are restricted to 30, 45, or 60 minutes.
4. The assignment's official business rules take priority over undocumented assumptions.
5. Generated CSV reports represent the program's calculated results.
6. The system does not require a graphical user interface.

## 5. Validation Decisions and Known Issues

### V01 — Automated Tests

The local test suite was executed using:

`python -m unittest test_main -v`

The latest recorded execution completed 23 tests successfully.

### V02 — Main Program Execution

The program was executed using:

`python main.py`

**Latest recorded results:**

- Requests processed: 80
- Session events: 147
- Payout rows: 59

### V03 — Tutor Selection Discrepancy

A sample-data discrepancy was identified involving tutors TU-015 and TU-009.

The official ranking formula selects TU-009 for the relevant sample request, whereas the accompanying example expects TU-015.

**Decision:** Preserve the specified ranking formula rather than hardcoding a tutor selection to match an inconsistent example.

**Status:** Documented; clarification may be required from the evaluators.

### V04 — Hidden Evaluation Cases

The evaluators' hidden test inputs are not available to the development team.

**Decision:** Validate using available sample data, automated tests, boundary checks, and documented edge cases.

**Limitation:** Complete hidden-case correctness cannot be guaranteed before evaluation.

## 6. Future Improvements

Potential extensions include:

- Database-backed session management
- Student and tutor web portals
- Real-time availability updates
- Payment gateway integration
- Expanded automated testing and validation
- Administrative monitoring and reporting

These are future enhancements rather than requirements of the current command-file-driven assignment.

## 7. Conclusion

The project uses a deterministic, rule-based architecture to automate tutor matching, session lifecycle management, pricing, and weekly financial settlement.

The design prioritizes reproducibility, clear business-rule mapping, and automated validation while documenting known limitations and assumptions.

---

**Team T050 — PS-103**  
**10 SECONDS Capstone Project**
