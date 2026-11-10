# Week 3 Validation Notes
## Team T050 | PS-103

### Automated Testing
- All 23 automated unit tests passed.
- Tests cover BR-01 through BR-12.
- Sample processing: 80 requests, 147 session events, 59 payout rows.

### Package Expiry
- Package: PKG-03
- Session date: 22 October 2026
- Expired package was rejected.
- Normal session price: Rs 700.00
- Result: PASS

### TU-015 Carryforward
- Gross earnings: Rs 932.00
- Commission (25%): Rs 233.00
- Tutor cancellation penalty: Rs 200.00
- Remaining payout: Rs 499.00
- Minimum payout threshold: Rs 500.00
- Expected carryforward: Rs 499.00
- Isolated unit test: PASS

### Sample Data Discrepancy
The sample documentation associates the Rs 499
carryforward scenario with tutor TU-015.

However, applying the prescribed matching formula
to the supplied tutor data selects TU-009 for the
relevant request instead.

Decision: Preserve the official matching formula
and deterministic ranking. Do not hardcode a tutor
selection to force the sample scenario.

### Remaining Verification
Passing tests do not guarantee correctness on all
hidden evaluation cases. Additional integration
testing may still reveal issues.
