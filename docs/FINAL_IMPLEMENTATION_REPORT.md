# FINAL IMPLEMENTATION REPORT

## T050 – PS-103: Online Tutoring Marketplace — Session Matching, Cancellation and Tutor Payout Engine

**Project ID:** PS-103  
**Team ID:** T050  
**Domain:** EdTech – Online Tutoring Marketplace  
**Programming Language:** Python 3.10+  
**Development Environment:** Visual Studio Code  
**Version Control:** GitHub  
**Project Status:** Implementation completed; final submission verification in progress

---

## 1. Project Overview

This project is a Python-based system designed to manage important activities of an online tutoring marketplace.

The system helps students find suitable tutors, manages tutoring sessions, calculates session charges, handles cancellations and rescheduling, and prepares weekly tutor payout reports.

Instead of manually performing these tasks, the program processes information from input files and generates the required results automatically.

The project focuses on implementing twelve business rules related to tutor matching, pricing, session management, tutor performance, and payments.

## 2. Project Objectives

The main objectives of the project are:

1. Match students with suitable tutors based on their requirements.
2. Rank eligible tutors using ratings, reliability, and hourly rates.
3. Calculate session charges and applicable discounts.
4. Manage session cancellations, refunds, and rescheduling.
5. Handle student and tutor no-show situations.
6. Calculate weekly platform commissions and tutor payouts.
7. Monitor tutor ratings, reliability, and suspension conditions.
8. Generate reports and validate the system using automated tests.

## 3. Technologies Used

- **Python 3.10+:** Used to implement the project logic.
- **Visual Studio Code:** Used for writing, running, and testing the program.
- **CSV files:** Used to store input data and generated results.
- **Python unittest:** Used for automated testing.
- **GitHub:** Used to maintain the project repository and documentation.

The project does not require a website or graphical user interface. It operates by reading input files and processing the provided instructions.

## 4. Project File Structure

The project contains the following main files and folders:

| File or Folder | Purpose |
|---|---|
| `main.py` | Main Python program |
| `test_main.py` | Automated test cases |
| `data/` | Input data and command files |
| `output/` | Generated result files |
| `docs/design.md` | Original design documentation |
| `docs/design.pdf` | Original design document in PDF format |
| `docs/DECISION_LOG.md` | Record of important design decisions |
| `docs/WEEK3_VALIDATION_NOTES.md` | Validation notes and observations |
| `README.md` | Project overview and execution instructions |

## 5. Implementation of the Twelve Business Rules

### BR-01: Tutor Eligibility

The system checks whether a tutor meets the student's requirements.

Matching conditions include subject, grade band, language, availability, and supported session duration.

Supported session durations are 30, 45, and 60 minutes.

### BR-02: Tutor Ranking

When multiple tutors are eligible, the system ranks them using a predefined formula.

The ranking considers tutor rating, reliability, and hourly rate.

If tutors have equal scores, the system applies tie-breaking rules based on confirmed sessions and tutor ID.

### BR-03: Surge Pricing

The system applies additional pricing during specified weekday evening hours when fewer than three eligible tutors are available.

The surge multiplier is 1.25.

Surge pricing is excluded for package sessions.

### BR-04: Session Packages

The system supports prepaid tutoring packages.

An 8-session package provides a 10% discount, while a 16-session package provides a 15% discount.

Packages are associated with a particular tutor and expire after 60 days.

### BR-05: Student Cancellation and Rescheduling

The system determines refunds based on how early a student cancels a session.

Cancellations more than 24 hours before the session receive a full refund.

Cancellations between 6 and 24 hours receive a 50% refund.

Cancellations less than 6 hours before the session receive no refund.

Free rescheduling is permitted only when the required conditions are satisfied.

### BR-06: Tutor Cancellation

The system applies reliability reductions and financial penalties when tutors cancel sessions.

The penalty depends on how close the cancellation is to the scheduled session.

Late tutor cancellations can also result in a discount coupon for the affected student.

### BR-07: No-Show Handling

The system handles situations where a student or tutor fails to attend a scheduled session.

Student no-shows can result in a full session charge after the required waiting period.

Tutor no-shows are treated as late tutor cancellations, with the applicable student refund.

### BR-08: Weekly Platform Commission

The platform commission depends on the number of completed sessions in a week.

- Fewer than 10 sessions: 25% commission.
- 10–24 sessions: 20% commission.
- 25 or more sessions: 15% commission.

### BR-09: Tutor Payout

The system calculates weekly tutor payouts after considering earnings, platform commission, penalties, and applicable tax deductions.

Payouts are scheduled for Wednesday.

Amounts below ₹500 are carried forward according to the payout rules.

### BR-10: Tutor Rating and Demotion

The system evaluates tutor performance using recent student ratings.

A tutor can be removed temporarily from automatic matching when the required low-rating conditions are met.

Matching eligibility can be restored after the specified number of completed direct-booking sessions.

### BR-11: Tutor Suspension

Tutors who repeatedly cancel sessions at short notice may be temporarily suspended from automatic matching.

The suspension period is 14 days when the specified cancellation threshold is reached.

### BR-12: Rule Precedence and Price Limits

The system applies the required sequence of matching and pricing rules.

Discounts and coupons are processed according to the specified order.

The final session price cannot be reduced below ₹100.

## 6. Input Data Processing

The program reads the provided input datasets and processes tutoring-related instructions.

These inputs include tutor information, student information, availability, session requests, and related records.

The program applies the required business rules and generates output files.

## 7. Generated Output Reports

The project generates three main CSV reports.

### 7.1 Matching Decisions

**File:** `output/match_decisions.csv`

This report records tutor matching decisions for student requests.

It helps show how the system processes eligibility and tutor selection.

### 7.2 Session Ledger

**File:** `output/session_ledger.csv`

This report records session-related events and their outcomes.

It supports the tracking of bookings, cancellations, rescheduling, and related financial calculations.

### 7.3 Tutor Payouts

**File:** `output/payouts.csv`

This report contains tutor payout calculations.

It supports the review of earnings, commissions, penalties, deductions, and payout amounts.

## 8. Program Execution

The main program can be executed from the project folder using:

`python main.py`

During the latest local execution, the program reported:

- Session requests processed: **80**
- Session events processed: **147**
- Payout rows generated: **59**

The generated reports were saved in the `output` folder.

These values describe the observed execution using the provided project data.

## 9. Automated Testing

The project uses Python's built-in `unittest` framework.

The automated test suite is located in `test_main.py`.

Tests can be executed using:

`python -m unittest test_main -v`

The latest local test execution reported:

**23 tests executed — all passed.**

The tests cover selected business-rule scenarios and boundary conditions.

Passing these tests confirms the expected behaviour for the tested cases. It does not independently guarantee that every possible hidden evaluation case will pass.

## 10. Mandatory Edge Cases

The project requirements identify eight important edge cases:

1. Equal tutor-ranking scores and tutor-ID tie-breaking.
2. Exactly three eligible tutors during the surge-pricing period.
3. A rescheduling request made exactly 12 hours before a session.
4. A weekly payout that crosses the annual ₹30,000 tax threshold.
5. A package that expires before a future session.
6. A tutor's tenth rating causing the average to fall below 3.5.
7. A ₹499 payout carried forward to the following week.
8. A discount coupon applied to a ₹110 session with a ₹100 minimum price.

These scenarios were considered during development and validation.

The detailed design expectations are documented in `docs/design.pdf`, while additional observations are recorded in `docs/WEEK3_VALIDATION_NOTES.md`.

## 11. Validation Notes and Known Limitations

The program successfully completed its latest local execution and passed the available automated tests.

One observation from sample-data validation concerns the expected tutor assignment and ₹499 carryforward scenario involving tutor TU-015.

The implemented ranking procedure can select a different eligible tutor for that request. An isolated synthetic test of the ₹499 carryforward rule passed, but that does not establish that the full official sample scenario matches every expected result.

This observation is documented rather than resolved by introducing a special-case tutor selection.

Further validation against additional unseen scenarios may identify issues not covered by the current tests.

## 12. Design Documentation

The original design document contains:

- Project information and objectives.
- Technologies and project scope.
- Project glossary.
- Class diagram.
- Session state diagram.
- All twelve business rules.
- Eight mandatory edge cases.

The original document is retained as `docs/design.pdf`.

This final implementation report supplements that document with implementation status, observed execution results, automated testing information, and validation notes.

## 13. Demonstration Video

The project demonstration video shows the execution of the Python program, generated CSV reports, and automated testing.

**Video link:**

https://drive.google.com/file/d/1lAFzZbTM95E2tJeGI8-FQUTGxuptSB5d/view?usp=sharing

## 14. Conclusion

The Online Tutoring Marketplace project demonstrates how Python can be used to automate important operations of an online tutoring platform.

The system processes tutor matching, session management, pricing, cancellations, and tutor payouts using predefined business rules.

The project includes input datasets, generated reports, design documentation, and automated tests.

The latest local execution completed successfully, and all 23 available automated tests passed.

The implementation is ready for final documentation review and submission, subject to the remaining verification requirements.