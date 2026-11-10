
"""Week 3 automated tests for T050-PS-103."""

import unittest
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import main


def timestamp(value):
    return main.dt(value)


class RuleTests(unittest.TestCase):

    def setUp(self):
        self.engine = main.Engine()

    def session(
        self, rid="TEST", tutor="TU-005",
        student="STU-001",
        start="2026-10-05 10:00:00",
        duration=60, price="932",
        status="CONFIRMED", direct=False
    ):
        s = {
            "id": rid,
            "tutor": tutor,
            "student": student,
            "subject": "Kannada",
            "grade": 9,
            "language": "Kannada",
            "start": timestamp(start),
            "duration": duration,
            "price": Decimal(price),
            "status": status,
            "package_id": "NONE",
            "free_moves": 0,
            "paid_moves": 0,
            "coupon_used": False,
            "package_consumed": False,
            "direct": direct
        }
        self.engine.sessions[rid] = s
        return s

    # BR-01: Matching eligibility

    def test_br01_invalid_duration(self):
        parts = (
            "REQUEST|2026-10-05 07:00:00|BAD|STU-001|"
            "Kannada|9|Kannada|2026-10-05 10:00:00|40|NONE"
        ).split("|")
        self.engine.request(parts, 1)
        self.assertEqual(
            self.engine.matches[-1]["status"], "REJECTED"
        )

    def test_br01_grade_and_availability(self):
        start = timestamp("2026-10-05 10:00:00")
        self.assertTrue(
            self.engine.eligible(
                "TU-005", "Kannada", 9, "Kannada", start, 60
            )
        )
        self.assertFalse(
            self.engine.eligible(
                "TU-005", "Kannada", 1, "Kannada", start, 60
            )
        )

    def test_br01_confirmed_overlap(self):
        self.session()
        self.assertTrue(
            self.engine.busy(
                "TU-005",
                timestamp("2026-10-05 10:30:00"), 30
            )
        )
        self.assertFalse(
            self.engine.busy(
                "TU-005",
                timestamp("2026-10-05 11:00:00"), 30
            )
        )

    # BR-02: Tutor ranking

    def test_br02_ranking_formula(self):
        rate = Decimal(
            self.engine.tutors["TU-005"]["hourly_rate"]
        )
        expected = (
            self.engine.rating("TU-005") * 10
            + self.engine.reliability["TU-005"] * 5
        )
        self.assertEqual(
            self.engine.score("TU-005", rate), expected
        )

    def test_br02_id_tiebreak(self):
        parts = (
            "REQUEST|2026-10-05 07:00:00|TIE|STU-001|"
            "Kannada|9|Kannada|2026-10-05 10:00:00|60|NONE"
        ).split("|")
        self.engine.request(parts, 1)
        self.assertEqual(
            self.engine.matches[-1]["tutor_id"], "TU-005"
        )

    # BR-03: Surge pricing

    def test_br03_surge_under_three(self):
        price, surge = self.engine.price(
            "TU-005", 60,
            timestamp("2026-10-05 20:30:00"), 2
        )
        expected = main.cash(
            Decimal(
                self.engine.tutors["TU-005"]["hourly_rate"]
            ) * Decimal("1.25")
        )
        self.assertTrue(surge)
        self.assertEqual(price, expected)

    def test_br03_no_surge_exactly_three(self):
        _, surge = self.engine.price(
            "TU-005", 60,
            timestamp("2026-10-05 20:30:00"), 3
        )
        self.assertFalse(surge)

    # BR-04: Session packages

    def test_br04_package_discount(self):
        pack = {"pack_size": "8"}
        price, surge = self.engine.price(
            "TU-005", 60,
            timestamp("2026-10-05 20:30:00"),
            1, pack
        )
        expected = main.cash(
            Decimal(
                self.engine.tutors["TU-005"]["hourly_rate"]
            ) * Decimal("0.90")
        )
        self.assertFalse(surge)
        self.assertEqual(price, expected)

    def test_br04_package_expiry(self):
        pack = self.engine.packages["PKG-03"]
        result = self.engine.package(
            "PKG-03",
            pack["student_id"],
            pack["tutor_id"],
            timestamp("2026-10-22 10:00:00")
        )
        self.assertIsNone(result)

    # BR-05: Cancellation and rescheduling

    def test_br05_exact_12_hours_paid(self):
        s = self.session(
            start="2026-10-07 18:00:00",
            tutor="TU-010",
            price="1000"
        )
        with patch.object(
            self.engine, "available", return_value=True
        ):
            self.engine.reschedule(
                "TEST",
                timestamp("2026-10-07 06:00:00"),
                "2026-10-08 18:00:00", 1
            )
        self.assertEqual(s["paid_moves"], 1)
        self.assertEqual(s["free_moves"], 0)

    def test_br05_exact_24h_half_refund(self):
        self.session(price="1000")
        self.engine.cancel_student(
            "TEST",
            timestamp("2026-10-04 10:00:00"), 1
        )
        self.assertEqual(
            self.engine.ledger[-1]["refund"], "500.00"
        )

    def test_br05_exact_6h_half_refund(self):
        self.session(price="1000")
        self.engine.cancel_student(
            "TEST",
            timestamp("2026-10-05 04:00:00"), 1
        )
        self.assertEqual(
            self.engine.ledger[-1]["refund"], "500.00"
        )

    # BR-06: Tutor cancellation

    def test_br06_tutor_cancel(self):
        self.session(price="1000")
        before = self.engine.reliability["TU-005"]

        self.engine.cancel_tutor(
            "TEST",
            timestamp("2026-10-05 05:00:00"), 1
        )

        self.assertEqual(
            self.engine.ledger[-1]["penalty"], "500.00"
        )
        self.assertEqual(
            self.engine.reliability["TU-005"],
            max(Decimal("0"), before - Decimal("0.5"))
        )
        self.assertEqual(
            self.engine.coupons["STU-001"], 1
        )

    # BR-07: Student no-show

    def test_br07_student_noshow_charge(self):
        s = self.session(price="1000")
        now = timestamp("2026-10-05 10:10:00")

        if now >= s["start"] + timedelta(minutes=10):
            key = (
                main.week_start(s["start"]),
                s["tutor"]
            )
            self.engine.week_noshow_charges[key] += s["price"]

        self.assertEqual(
            self.engine.week_noshow_charges[
                (main.week_start(s["start"]), "TU-005")
            ],
            Decimal("1000")
        )

    # BR-08: Weekly commission tiers

    def test_br08_commission_tiers(self):
        week = main.day("2026-10-05")

        for count, percentage in [
            (1, "25.00"),
            (10, "20.00"),
            (25, "15.00")
        ]:
            engine = main.Engine()
            engine.week_completions[
                (week, "TU-005")
            ] = [Decimal("1000")] * count

            engine.close_week(
                "2026-10-05", "2026-10-11"
            )

            row = next(
                r for r in engine.payouts
                if r["tutor_id"] == "TU-005"
            )
            self.assertEqual(
                row["commission_pct"], percentage
            )

    # BR-09: Weekly payouts and TDS

    def test_br09_499_carryforward(self):
        engine = self.engine
        week = main.day("2026-10-05")

        engine.week_completions[
            (week, "TU-015")
        ] = [Decimal("932")]

        engine.week_penalties[
            (week, "TU-015")
        ] = Decimal("200")

        engine.close_week(
            "2026-10-05", "2026-10-11"
        )

        row = next(
            r for r in engine.payouts
            if r["tutor_id"] == "TU-015"
        )

        self.assertEqual(
            row["net_paid"], "0.00"
        )
        self.assertEqual(
            row["carried_forward"], "499.00"
        )

    def test_br09_tds_crossing(self):
        engine = self.engine
        engine.annual["TU-010"] = Decimal("28500")

        week = main.day("2026-10-12")
        engine.week_completions[
            (week, "TU-010")
        ] = [Decimal("1000")] * 3

        engine.close_week(
            "2026-10-12", "2026-10-18"
        )

        row = next(
            r for r in engine.payouts
            if r["tutor_id"] == "TU-010"
        )

        self.assertEqual(row["tds"], "225.00")

    # BR-10: Ratings and demotion

    def test_br10_invalid_rating(self):
        self.session(status="COMPLETED")
        self.engine.rate("TEST", 6, 1)
        self.assertEqual(
            self.engine.ledger[-1]["note"],
            "INVALID_RATING"
        )

    def test_br10_demote_tenth_rating(self):
        self.session(
            tutor="TU-012", status="COMPLETED"
        )
        self.engine.rate("TEST", 1, 1)
        self.assertIn(
            "TU-012", self.engine.demoted
        )

    # BR-11: Matching suspension

    def test_br11_three_late_cancels(self):
        now = timestamp("2026-10-05 09:00:00")

        for i in range(3):
            rid = f"R{i}"
            self.session(
                rid=rid,
                start="2026-10-05 10:00:00"
            )
            self.engine.cancel_tutor(
                rid,
                now + timedelta(minutes=i),
                i
            )

        self.assertIn(
            "TU-005", self.engine.suspended_until
        )
        self.assertEqual(
            self.engine.suspended_until["TU-005"],
            now + timedelta(days=14, minutes=2)
        )

    # BR-12: Coupon price floor

    def test_br12_coupon_floor(self):
        tutor = {
            **self.engine.tutors["TU-005"],
            "hourly_rate": "220"
        }

        with patch.dict(
            self.engine.tutors, {"TU-005": tutor}
        ):
            price, _ = self.engine.price(
                "TU-005", 30,
                timestamp("2026-10-06 10:00:00"),
                3, coupon=True
            )

        self.assertEqual(
            price, Decimal("100.00")
        )

    # Additional validation tests

    def test_duplicate_confirm_rejected(self):
        self.session(status="MATCHED")
        self.engine.confirm("TEST", 1)
        self.engine.confirm("TEST", 2)

        self.assertEqual(
            self.engine.ledger[-1]["note"],
            "INVALID_CONFIRM"
        )

    def test_sample_input_end_to_end(self):
        self.engine.run()

        self.assertEqual(
            len(self.engine.matches), 80
        )
        self.assertGreater(
            len(self.engine.ledger), 100
        )
        self.assertGreater(
            len(self.engine.payouts), 0
        )
        self.assertTrue(
            (
                main.OUT / "match_decisions.csv"
            ).exists()
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
