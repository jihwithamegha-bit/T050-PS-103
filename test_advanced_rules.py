"""
Advanced business-rule tests for T050-PS-103.

Copy beside main.py. Run:
    python -m unittest test_advanced_rules -v

These tests use the current project's Engine and bundled CSV fixtures.
They modify only in-memory Engine state; they do not edit project files.
"""

import unittest
from datetime import timedelta
from decimal import Decimal

import main


class AdvancedBusinessRuleTests(unittest.TestCase):
    def setUp(self):
        self.engine = main.Engine()
        self.tutor_id = next(iter(self.engine.tutors))

    def add_session(
        self,
        request_id,
        *,
        tutor_id=None,
        start="2026-10-05 10:00:00",
        status="CONFIRMED",
        direct=False,
        price="1000.00",
    ):
        tutor_id = tutor_id or self.tutor_id
        session = {
            "id": request_id,
            "tutor": tutor_id,
            "student": "STU-001",
            "subject": "Kannada",
            "grade": 9,
            "language": "Kannada",
            "start": main.dt(start),
            "duration": 60,
            "price": Decimal(price),
            "status": status,
            "package_id": "NONE",
            "free_moves": 0,
            "paid_moves": 0,
            "coupon_used": False,
            "package_consumed": False,
            "direct": direct,
        }
        self.engine.sessions[request_id] = session
        return session

    def set_week_earnings(self, count, amount_each="1000.00",
                          week="2026-10-05"):
        week_date = main.day(week)
        self.engine.week_completions[(week_date, self.tutor_id)] = [
            Decimal(amount_each) for _ in range(count)
        ]
        return week_date

    # BR-08: tier boundaries apply to all sessions in the week.
    def test_commission_tier_below_ten_sessions_is_25_percent(self):
        self.set_week_earnings(9)
        self.engine.close_week("2026-10-05", "2026-10-11")
        row = self.engine.payouts[-1]
        self.assertEqual(row["commission_pct"], "25.00")

    def test_commission_tier_at_ten_sessions_is_20_percent(self):
        self.set_week_earnings(10)
        self.engine.close_week("2026-10-05", "2026-10-11")
        row = self.engine.payouts[-1]
        self.assertEqual(row["commission_pct"], "20.00")

    def test_commission_tier_at_twenty_four_sessions_is_20_percent(self):
        self.set_week_earnings(24)
        self.engine.close_week("2026-10-05", "2026-10-11")
        row = self.engine.payouts[-1]
        self.assertEqual(row["commission_pct"], "20.00")

    def test_commission_tier_at_twenty_five_sessions_is_15_percent(self):
        self.set_week_earnings(25)
        self.engine.close_week("2026-10-05", "2026-10-11")
        row = self.engine.payouts[-1]
        self.assertEqual(row["commission_pct"], "15.00")

    # BR-09: TDS is triggered only when the cumulative amount crosses 30,000.
    def test_tds_not_applied_when_cumulative_payable_is_exactly_30000(self):
        self.engine.annual[self.tutor_id] = Decimal("0.00")
        self.set_week_earnings(1, "40000.00")
        self.engine.close_week("2026-10-05", "2026-10-11")
        row = self.engine.payouts[-1]
        self.assertEqual(row["tds"], "0.00")
        self.assertEqual(row["net_paid"], "30000.00")

    def test_tds_applies_to_entire_crossing_payout(self):
        self.engine.annual[self.tutor_id] = Decimal("1000.00")
        self.set_week_earnings(1, "40000.00")
        self.engine.close_week("2026-10-05", "2026-10-11")
        row = self.engine.payouts[-1]
        self.assertEqual(row["commission_pct"], "25.00")
        self.assertEqual(row["commission"], "10000.00")
        self.assertEqual(row["tds"], "3000.00")
        self.assertEqual(row["net_paid"], "27000.00")

    # BR-09: Minimum payout boundary.
    def test_exactly_500_payable_is_released(self):
        self.set_week_earnings(1, "666.67")
        self.engine.close_week("2026-10-05", "2026-10-11")
        row = self.engine.payouts[-1]
        self.assertEqual(row["net_paid"], "500.00")
        self.assertEqual(row["carried_forward"], "0.00")

    def test_payable_below_500_is_carried_forward(self):
        self.set_week_earnings(1, "665.32")
        self.engine.close_week("2026-10-05", "2026-10-11")
        row = self.engine.payouts[-1]
        self.assertEqual(row["net_paid"], "0.00")
        self.assertEqual(row["carried_forward"], "498.99")

    # BR-06: Reliability remains within the documented 0..5 range.
    def test_completion_never_increases_reliability_above_five(self):
        session = self.add_session("REL-UP", status="CONFIRMED")
        self.engine.reliability[session["tutor"]] = Decimal("4.99")
        self.engine.complete("REL-UP", 1)
        self.assertEqual(
            self.engine.reliability[session["tutor"]], Decimal("5")
        )

    def test_late_cancellation_never_reduces_reliability_below_zero(self):
        session = self.add_session("REL-DOWN", status="CONFIRMED")
        self.engine.reliability[session["tutor"]] = Decimal("0.20")
        now = session["start"] - timedelta(hours=2)
        self.engine.cancel_tutor("REL-DOWN", now, 1)
        self.assertEqual(
            self.engine.reliability[session["tutor"]], Decimal("0")
        )

    # BR-11: Three late cancellations within 30 days trigger 14-day suspension.
    def test_third_late_cancellation_triggers_fourteen_day_suspension(self):
        tutor = self.tutor_id
        dates = [
            "2026-10-05 10:00:00",
            "2026-10-15 10:00:00",
            "2026-10-25 10:00:00",
        ]
        for index, start_text in enumerate(dates, start=1):
            session_id = f"LATE-{index}"
            session = self.add_session(
                session_id, tutor_id=tutor, start=start_text
            )
            now = session["start"] - timedelta(hours=2)
            self.engine.cancel_tutor(session_id, now, index)

        expected_until = main.dt("2026-10-25 08:00:00") + timedelta(days=14)
        self.assertEqual(self.engine.suspended_until[tutor], expected_until)

    def test_suspension_blocks_automatic_matching_but_not_direct_eligibility(self):
        tutor = self.tutor_id
        self.engine.suspended_until[tutor] = main.dt("2026-12-01 00:00:00")
        self.engine.available = lambda *args, **kwargs: True
        self.engine.busy = lambda *args, **kwargs: False
        start = main.dt("2026-11-20 10:00:00")
        request_time = main.dt("2026-11-16 10:00:00")
        row = self.engine.tutors[tutor]
        subject = row["subjects"].split(";")[0]
        language = row["languages"].split(";")[0]
        band = row["grade_bands"].split(";")[0]
        grade = int(band.split("-")[0])

        self.assertFalse(
            self.engine.eligible(
                tutor, subject, grade, language, start, 30,
                request_time=request_time,
            )
        )
        self.assertTrue(
            self.engine.eligible(
                tutor, subject, grade, language, start, 30,
                direct=True, request_time=request_time,
            )
        )

    def test_confirmed_booking_remains_in_session_store_after_suspension(self):
        tutor = self.tutor_id
        session = self.add_session("EXISTING-CONFIRMED", tutor_id=tutor)
        self.engine.suspended_until[tutor] = main.dt("2026-12-01 00:00:00")
        self.assertEqual(session["status"], "CONFIRMED")
        self.assertIn("EXISTING-CONFIRMED", self.engine.sessions)

    # BR-05: exactly 12 hours is not eligible for a free reschedule.
    def test_reschedule_at_exactly_twelve_hours_is_paid_not_free(self):
        session = self.add_session(
            "RESCHED-12H",
            start="2026-10-05 22:00:00",
            status="CONFIRMED",
        )
        now = main.dt("2026-10-05 10:00:00")
        new_start = "2026-10-06 10:00:00"

        # Isolate the reschedule notice boundary from schedule data.
        self.engine.available = lambda *args, **kwargs: True
        self.engine.busy = lambda *args, **kwargs: False
        self.engine.price = lambda *args, **kwargs: (Decimal("1000.00"), False)

        self.engine.reschedule("RESCHED-12H", now, new_start, 1)

        self.assertEqual(session["free_moves"], 0)
        self.assertEqual(session["paid_moves"], 1)
        self.assertEqual(session["start"], main.dt(new_start))
        self.assertTrue(
            self.engine.ledger[-1]["note"].startswith("PAID_RESCHEDULE_FROM_")
        )

    def test_closed_week_cannot_be_paid_twice(self):
        self.set_week_earnings(1, "1000.00")
        self.engine.close_week("2026-10-05", "2026-10-11")
        first = list(self.engine.payouts)
        self.engine.close_week("2026-10-05", "2026-10-11")
        self.assertEqual(self.engine.payouts, first)


if __name__ == "__main__":
    unittest.main(verbosity=2)
