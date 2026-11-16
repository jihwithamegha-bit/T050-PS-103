"""Additional edge-case tests for T050-PS-103. Run: python -m unittest test_edge_cases -v"""
import unittest
from decimal import Decimal
import main


class AdditionalEdgeCaseTests(unittest.TestCase):
    def setUp(self):
        self.engine = main.Engine()

    def make_session(self, request_id="EDGE", tutor_id="TU-005",
                     start="2026-10-05 10:00:00", duration=60,
                     status="CONFIRMED", price="1000.00"):
        session = {
            "id": request_id, "tutor": tutor_id, "student": "STU-001",
            "subject": "Kannada", "grade": 9, "language": "Kannada",
            "start": main.dt(start), "duration": duration,
            "price": Decimal(price), "status": status,
            "package_id": "NONE", "free_moves": 0, "paid_moves": 0,
            "coupon_used": False, "package_consumed": False, "direct": False,
        }
        self.engine.sessions[request_id] = session
        return session

    def request_parts(self, request_id="EDGE-REQUEST", student="STU-001",
                      subject="Kannada", grade="9", duration="60"):
        return (f"REQUEST|2026-10-05 07:00:00|{request_id}|{student}|"
                f"{subject}|{grade}|Kannada|2026-10-05 10:00:00|{duration}|NONE").split("|")

    def test_adjacent_sessions_do_not_overlap(self):
        self.make_session()
        self.assertFalse(self.engine.busy("TU-005", main.dt("2026-10-05 11:00:00"), 30))

    def test_cancelled_session_does_not_block_tutor(self):
        self.make_session(status="CANCELLED_STUDENT")
        self.assertFalse(self.engine.busy("TU-005", main.dt("2026-10-05 10:30:00"), 30))

    def test_other_tutor_booking_does_not_block(self):
        self.make_session(tutor_id="TU-010")
        self.assertFalse(self.engine.busy("TU-005", main.dt("2026-10-05 10:30:00"), 30))

    def test_unknown_student_is_rejected(self):
        self.engine.request(self.request_parts(student="STU-UNKNOWN"), 1)
        self.assertEqual(self.engine.matches[-1]["status"], "REJECTED")

    def test_grade_zero_is_rejected(self):
        self.engine.request(self.request_parts(grade="0"), 1)
        self.assertEqual(self.engine.matches[-1]["status"], "REJECTED")

    def test_grade_above_twelve_is_rejected(self):
        self.engine.request(self.request_parts(grade="13"), 1)
        self.assertEqual(self.engine.matches[-1]["status"], "REJECTED")

    def test_blank_subject_is_rejected(self):
        self.engine.request(self.request_parts(subject="   "), 1)
        self.assertEqual(self.engine.matches[-1]["status"], "REJECTED")

    def test_duplicate_request_id_is_rejected(self):
        self.engine.request(self.request_parts(request_id="DUP"), 1)
        self.assertIn("DUP", self.engine.sessions)
        self.engine.request(self.request_parts(request_id="DUP"), 2)
        self.assertEqual(self.engine.matches[-1]["status"], "REJECTED")

    def test_unknown_package_is_rejected(self):
        result = self.engine.package("NO-SUCH-PACKAGE", "STU-001", "TU-005",
                                     main.dt("2026-10-05 10:00:00"))
        self.assertIsNone(result)

    def test_package_wrong_owner_is_rejected(self):
        package_id, package = next(iter(self.engine.packages.items()))
        when = main.dt(package["purchase_date"] + " 10:00:00")
        result = self.engine.package(package_id, "NOT-THE-OWNER",
                                     package["tutor_id"], when)
        self.assertIsNone(result)

    def test_exhausted_package_is_rejected(self):
        package_id, package = next(iter(self.engine.packages.items()))
        self.engine.pack_uses[package_id] = int(package["pack_size"])
        when = main.dt(package["purchase_date"] + " 10:00:00")
        result = self.engine.package(package_id, package["student_id"],
                                     package["tutor_id"], when)
        self.assertIsNone(result)

    def test_unconfirmed_session_cannot_be_completed(self):
        self.make_session(status="MATCHED")
        self.engine.complete("EDGE", 1)
        self.assertEqual(self.engine.sessions["EDGE"]["status"], "MATCHED")
        self.assertEqual(self.engine.ledger[-1]["note"], "INVALID_STATE")

    def test_second_completion_does_not_add_duplicate_earning(self):
        session = self.make_session(status="CONFIRMED")
        self.engine.complete("EDGE", 1)
        self.engine.complete("EDGE", 2)
        key = (main.week_start(session["start"]), "TU-005")
        self.assertEqual(len(self.engine.week_completions[key]), 1)
        self.assertEqual(self.engine.ledger[-1]["note"], "INVALID_STATE")

    def test_duplicate_rating_is_rejected(self):
        self.make_session(status="COMPLETED")
        self.engine.rate("EDGE", 5, 1)
        count = len(self.engine.ratings["TU-005"])
        self.engine.rate("EDGE", 4, 2)
        self.assertEqual(len(self.engine.ratings["TU-005"]), count)
        self.assertEqual(self.engine.ledger[-1]["note"], "INVALID_RATING")

    def test_coupon_price_floor(self):
        tutor = dict(self.engine.tutors["TU-005"])
        tutor["hourly_rate"] = "1"
        self.engine.tutors["TU-005"] = tutor
        price, _ = self.engine.price("TU-005", 30,
                                     main.dt("2026-10-06 10:00:00"),
                                     3, coupon=True)
        self.assertEqual(price, Decimal("100.00"))

    def test_week_close_is_idempotent(self):
        week = main.day("2026-10-05")
        self.engine.week_completions[(week, "TU-005")] = [Decimal("1000.00")]
        self.engine.close_week("2026-10-05", "2026-10-11")
        first = list(self.engine.payouts)
        self.engine.close_week("2026-10-05", "2026-10-11")
        self.assertEqual(self.engine.payouts, first)


if __name__ == "__main__":
    unittest.main(verbosity=2)
