
import csv
from collections import defaultdict, deque
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "output"
ZERO = Decimal("0")


def dec(value):
    return Decimal(str(value))


def cash(value):
    return dec(value).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def fmt(value):
    return f"{cash(value):.2f}"


def dt(value):
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def day(value):
    return date.fromisoformat(value)


def read_csv(filename):
    with (DATA / filename).open(
        newline="", encoding="utf-8-sig"
    ) as file:
        return list(csv.DictReader(file))


def write_csv(filename, columns, rows):
    OUT.mkdir(exist_ok=True)

    with (OUT / filename).open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=columns, extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


def week_start(value):
    d = value.date() if isinstance(value, datetime) else value
    return d - timedelta(days=d.weekday())


def overlap(a, b, c, d):
    return a < d and c < b


class Engine:

    def __init__(self):
        self.tutors = {
            row["tutor_id"]: row
            for row in read_csv("tutors.csv")
        }

        self.students = {
            row["student_id"]: row
            for row in read_csv("students.csv")
        }

        self.availability = read_csv("availability.csv")

        self.packages = {
            row["package_id"]: row
            for row in read_csv("packages.csv")
        }

        self.pack_uses = defaultdict(int)
        self.ratings = defaultdict(lambda: deque(maxlen=20))

        history = sorted(
            read_csv("rating_history.csv"),
            key=lambda r: (r["tutor_id"], int(r["seq"]))
        )

        for row in history:
            self.ratings[row["tutor_id"]].append(
                int(row["rating"])
            )

        self.reliability = {
            tid: dec(tutor["reliability"])
            for tid, tutor in self.tutors.items()
        }

        self.annual = {
            tid: dec(tutor["annual_payout_to_date"])
            for tid, tutor in self.tutors.items()
        }

        self.suspended_until = {}
        self.late_cancels = defaultdict(list)
        self.demoted = set()
        self.demoted_progress = defaultdict(int)
        self.coupons = defaultdict(int)

        self.sessions = {}
        self.matches = []
        self.ledger = []
        self.payouts = []

        self.week_completions = defaultdict(list)
        self.week_noshow_charges = defaultdict(lambda: ZERO)
        self.week_penalties = defaultdict(lambda: ZERO)
        self.carry = defaultdict(lambda: ZERO)
        self.closed_weeks = set()

    # ---------- TUTOR RATING ----------

    def rating(self, tutor_id):
        history = self.ratings[tutor_id]

        if history:
            return sum(map(dec, history)) / len(history)

        return dec(self.tutors[tutor_id]["rating"])

    # ---------- AVAILABILITY ----------

    def available(self, tutor_id, start, minutes):
        end = start + timedelta(minutes=minutes)
        weekday = start.strftime("%a").upper()

        for slot in self.availability:
            if slot["tutor_id"] != tutor_id:
                continue

            if slot["weekday"].upper() != weekday:
                continue

            available_from = dt(
                start.strftime("%Y-%m-%d ")
                + slot["from_time"]
            )

            available_to = dt(
                start.strftime("%Y-%m-%d ")
                + slot["to_time"]
            )

            if available_from <= start and end <= available_to:
                return True

        return False

    # ---------- BOOKING CONFLICT ----------

    def busy(self, tutor_id, start, minutes, except_id=None):
        end = start + timedelta(minutes=minutes)

        for session in self.sessions.values():
            if session["id"] == except_id:
                continue

            if session["tutor"] != tutor_id:
                continue

            if session["status"] != "CONFIRMED":
                continue

            other_start = session["start"]
            other_end = other_start + timedelta(
                minutes=session["duration"]
            )

            if overlap(start, end, other_start, other_end):
                return True

        return False

    # ---------- PACKAGE VALIDATION ----------

    def package(self, package_id, student_id, tutor_id, start):
        package = self.packages.get(package_id)

        if not package:
            return None

        if package["student_id"] != student_id:
            return None

        if package["tutor_id"] != tutor_id:
            return None

        purchased = day(package["purchase_date"])
        expiry = purchased + timedelta(days=60)

        if not purchased <= start.date() <= expiry:
            return None

        if self.pack_uses[package_id] >= int(
            package["pack_size"]
        ):
            return None

        return package

    # ---------- TUTOR ELIGIBILITY ----------

    def eligible(
        self, tutor_id, subject, grade,
        language, start, minutes, direct=False, request_time=None
    ):
        tutor = self.tutors[tutor_id]

        if not direct:
            if tutor_id in self.demoted:
                return False

            if (request_time or start) < self.suspended_until.get(
                tutor_id, datetime.min
            ):
                return False

        if subject not in tutor["subjects"].split(";"):
            return False

        if language not in tutor["languages"].split(";"):
            return False

        grade_ok = False

        for band in tutor["grade_bands"].split(";"):
            low, high = map(int, band.split("-"))

            if low <= grade <= high:
                grade_ok = True

        if not grade_ok:
            return False

        return (
            self.available(tutor_id, start, minutes)
            and not self.busy(tutor_id, start, minutes)
        )

    # ---------- WEEKLY CONFIRMED COUNT ----------

    def weekly_confirmed(self, tutor_id, request_time):
        week = week_start(request_time)

        return sum(
            1 for session in self.sessions.values()
            if session["tutor"] == tutor_id
            and session["status"] == "CONFIRMED"
            and week_start(session["start"]) == week
        )

    # ---------- RANKING SCORE ----------

    def score(self, tutor_id, cheapest_rate):
        tutor = self.tutors[tutor_id]

        return (
            self.rating(tutor_id) * 10
            + self.reliability[tutor_id] * 5
            - (
                dec(tutor["hourly_rate"]) - cheapest_rate
            ) / 100
        )

    # ---------- SESSION PRICING ----------

    def price(
        self, tutor_id, minutes, start,
        eligible_count, package=None, coupon=False
    ):
        rate = dec(self.tutors[tutor_id]["hourly_rate"])
        price = rate * minutes / 60

        surge = False

        if package:
            if int(package["pack_size"]) == 8:
                price *= dec("0.90")
            else:
                price *= dec("0.85")

        elif (
            start.weekday() < 5
            and 18 <= start.hour < 21
            and eligible_count < 3
        ):
            price *= dec("1.25")
            surge = True

        if coupon:
            price *= dec("0.80")

        price = max(dec("100"), price)

        return cash(price), surge

    # ---------- SESSION LEDGER ----------

    def log(
        self, line, request_id, event,
        note="", amount=ZERO, refund=ZERO, penalty=ZERO
    ):
        session = self.sessions.get(request_id)

        tutor_id = session["tutor"] if session else ""

        reliability = (
            fmt(self.reliability[tutor_id])
            if tutor_id else "0.00"
        )

        self.ledger.append({
            "line_no": line,
            "request_id": request_id,
            "event": event,
            "tutor_id": tutor_id,
            "amount_to_student": fmt(amount),
            "refund": fmt(refund),
            "penalty": fmt(penalty),
            "reliability_after": reliability,
            "note": note
        })

    # ---------- REQUEST AND MATCHING ----------

    def request(self, parts, line):
        (
            _, timestamp, request_id, student_id,
            subject, grade, language,
            start_text, duration, package_id
        ) = parts

        now = dt(timestamp)
        start = dt(start_text)
        minutes = int(duration)
        grade = int(grade)

        result = {
            "request_id": request_id,
            "status": "NO_MATCH",
            "tutor_id": "",
            "score": "",
            "eligible_count": 0,
            "surge_applied": "false",
            "price": "0.00"
        }

        if (
            request_id in self.sessions
            or student_id not in self.students
            or minutes not in (30, 45, 60)
            or start <= now
        ):
            result["status"] = "REJECTED"
            self.matches.append(result)
            return

        candidates = [
            tutor_id for tutor_id in self.tutors
            if self.eligible(
                tutor_id, subject, grade,
                language, start, minutes, request_time=now
            )
        ]

        result["eligible_count"] = len(candidates)

        # Valid packages must use their assigned tutor.
        # Expired or invalid packages use normal matching.
        valid_package = None

        if package_id != "NONE":
            linked = self.packages.get(package_id)

            if linked and linked["student_id"] == student_id:
                linked_tutor = linked["tutor_id"]

                valid_package = self.package(
                    package_id, student_id, linked_tutor, start
                )

                if valid_package:
                    candidates = [
                        tid for tid in candidates
                        if tid == linked_tutor
                    ]

        if not candidates:
            self.matches.append(result)
            return

        # Cheapest among all eligible tutors.
        all_eligible = [
            tid for tid in self.tutors
            if self.eligible(
                tid, subject, grade, language, start, minutes,
                request_time=now
            )
        ]

        cheapest = min(
            dec(self.tutors[tid]["hourly_rate"])
            for tid in all_eligible
        )

        best = min(
            candidates,
            key=lambda tid: (
                -self.score(tid, cheapest),
                self.weekly_confirmed(tid, now),
                tid
            )
        )

        package = valid_package
        coupon = self.coupons[student_id] > 0

        price, surge = self.price(
            best, minutes, start,
            result["eligible_count"], package, coupon
        )

        if coupon:
            self.coupons[student_id] -= 1

        self.sessions[request_id] = {
            "id": request_id,
            "student": student_id,
            "tutor": best,
            "subject": subject,
            "grade": grade,
            "language": language,
            "start": start,
            "duration": minutes,
            "price": price,
            "status": "MATCHED",
            "package_id": (
                package_id if package else "NONE"
            ),
            "free_moves": 0,
            "paid_moves": 0,
            "coupon_used": coupon,
            "package_consumed": False,
            "direct": False
        }

        result.update({
            "status": "MATCHED",
            "tutor_id": best,
            "score": fmt(self.score(best, cheapest)),
            "surge_applied": str(surge).lower(),
            "price": fmt(price)
        })

        self.matches.append(result)

    # ---------- CONFIRM SESSION ----------

    def confirm(self, request_id, line):
        session = self.sessions.get(request_id)

        if (
            not session
            or session["status"] != "MATCHED"
            or self.busy(
                session["tutor"],
                session["start"],
                session["duration"],
                request_id
            )
        ):
            self.log(
                line, request_id, "CONFIRM",
                "INVALID_CONFIRM"
            )
            return

        session["status"] = "CONFIRMED"

        if session["package_id"] != "NONE":
            self.pack_uses[session["package_id"]] += 1
            session["package_consumed"] = True

        self.log(
            line, request_id, "CONFIRM",
            "CONFIRMED", amount=session["price"]
        )

    # ---------- STUDENT CANCELLATION ----------

    def cancel_student(
        self, request_id, now, line,
        event="CANCEL_STUDENT"
    ):
        session = self.sessions.get(request_id)

        if not session or session["status"] != "CONFIRMED":
            self.log(
                line, request_id, event, "INVALID_STATE"
            )
            return

        hours = (
            session["start"] - now
        ).total_seconds() / 3600

        if hours > 24:
            fraction = dec("1")
        elif hours >= 6:
            fraction = dec("0.5")
        else:
            fraction = ZERO

        refund = cash(session["price"] * fraction)
        session["status"] = "CANCELLED_STUDENT"

        self.log(
            line, request_id, event,
            "STUDENT_CANCEL", refund=refund
        )

    # ---------- TUTOR CANCELLATION ----------

    def cancel_tutor(
        self, request_id, now, line,
        event="CANCEL_TUTOR"
    ):
        session = self.sessions.get(request_id)

        if not session or session["status"] != "CONFIRMED":
            self.log(
                line, request_id, event, "INVALID_STATE"
            )
            return

        hours = (
            session["start"] - now
        ).total_seconds() / 3600

        if hours > 24:
            reduction = dec("0.1")
            penalty = ZERO

        elif hours >= 6:
            reduction = dec("0.3")
            penalty = dec("200")

        else:
            reduction = dec("0.5")
            penalty = dec("500")

            self.coupons[session["student"]] += 1

            tutor_id = session["tutor"]

            recent = [
                t for t in self.late_cancels[tutor_id]
                if timedelta(0) <= now - t <= timedelta(days=30)
            ]

            recent.append(now)
            self.late_cancels[tutor_id] = recent

            if len(recent) >= 3:
                until = now + timedelta(days=14)

                self.suspended_until[tutor_id] = max(
                    self.suspended_until.get(
                        tutor_id, datetime.min
                    ),
                    until
                )

        tutor_id = session["tutor"]

        self.reliability[tutor_id] = max(
            ZERO,
            self.reliability[tutor_id] - reduction
        )

        week = week_start(now)

        self.week_penalties[
            (week, tutor_id)
        ] += penalty

        session["status"] = "CANCELLED_TUTOR"

        note = (
            "TUTOR_NOSHOW"
            if event == "NOSHOW_TUTOR"
            else "TUTOR_CANCEL"
        )

        self.log(
            line, request_id, event,
            note,
            refund=session["price"],
            penalty=penalty
        )

    # ---------- RESCHEDULE SESSION ----------

    def reschedule(
        self, request_id, now, new_start_text, line
    ):
        session = self.sessions.get(request_id)

        if not session or session["status"] != "CONFIRMED":
            self.log(
                line, request_id,
                "RESCHEDULE", "INVALID_STATE"
            )
            return

        new_start = dt(new_start_text)

        hours = (
            session["start"] - now
        ).total_seconds() / 3600

        free = (
            hours > 12
            and session["free_moves"] < 2
            and now < new_start
            and new_start <= (
                session["start"] + timedelta(days=7)
            )
        )

        allowed = (
            new_start > now
            and self.available(
                session["tutor"],
                new_start,
                session["duration"]
            )
            and not self.busy(
                session["tutor"],
                new_start,
                session["duration"],
                request_id
            )
        )

        if not allowed:
            self.log(
                line, request_id,
                "RESCHEDULE", "NEW_SLOT_UNAVAILABLE"
            )
            return

        if free:
            session["free_moves"] += 1
            session["start"] = new_start

            self.log(
                line, request_id,
                "RESCHEDULE", "FREE_RESCHEDULE"
            )

        else:
            old_start = session["start"]

            if hours > 24:
                fraction = dec("1")
            elif hours >= 6:
                fraction = dec("0.5")
            else:
                fraction = ZERO

            refund = cash(
                session["price"] * fraction
            )

            count = sum(
                1 for tid in self.tutors
                if self.eligible(
                    tid,
                    session["subject"],
                    session["grade"],
                    session["language"],
                    new_start,
                    session["duration"],
                    request_time=now
                )
            )

            new_price, _ = self.price(
                session["tutor"],
                session["duration"],
                new_start,
                count
            )

            session["start"] = new_start
            session["price"] = new_price
            session["paid_moves"] += 1

            self.log(
                line,
                request_id,
                "RESCHEDULE",
                f"PAID_RESCHEDULE_FROM_{old_start}",
                amount=new_price,
                refund=refund
            )

    # ---------- COMPLETE SESSION ----------

    def complete(self, request_id, line):
        session = self.sessions.get(request_id)

        if not session or session["status"] != "CONFIRMED":
            self.log(
                line, request_id,
                "COMPLETE", "INVALID_STATE"
            )
            return

        session["status"] = "COMPLETED"
        tutor_id = session["tutor"]

        self.reliability[tutor_id] = min(
            dec("5"),
            self.reliability[tutor_id] + dec("0.05")
        )

        week = week_start(session["start"])

        self.week_completions[
            (week, tutor_id)
        ].append(session["price"])

        if tutor_id in self.demoted and session["direct"]:
            self.demoted_progress[tutor_id] += 1

            if self.demoted_progress[tutor_id] >= 5:
                self.demoted.remove(tutor_id)
                self.demoted_progress[tutor_id] = 0

        self.log(
            line, request_id,
            "COMPLETE", "COMPLETED",
            amount=session["price"]
        )

    # ---------- RATE TUTOR ----------

    def rate(self, request_id, value, line):
        session = self.sessions.get(request_id)

        if (
            not session
            or session["status"] != "COMPLETED"
            or session.get("rated")
            or not 1 <= value <= 5
        ):
            self.log(
                line, request_id,
                "RATE", "INVALID_RATING"
            )
            return

        tutor_id = session["tutor"]

        self.ratings[tutor_id].append(value)
        session["rated"] = True

        if (
            len(self.ratings[tutor_id]) >= 10
            and self.rating(tutor_id) < dec("3.5")
        ):
            self.demoted.add(tutor_id)
            self.demoted_progress[tutor_id] = 0

        self.log(
            line, request_id,
            "RATE", f"RATED_{value}"
        )

    # ---------- WEEKLY PAYOUT ----------

    def close_week(self, start_text, end_text):
        week = day(start_text)

        if week in self.closed_weeks:
            return

        self.closed_weeks.add(week)

        active = sorted(
            {
                tutor_id
                for (w, tutor_id) in (
                    set(self.week_completions)
                    | set(self.week_penalties)
                    | set(self.week_noshow_charges)
                )
                if w == week
            }
            | {
                tutor_id
                for tutor_id, amount in self.carry.items()
                if amount != ZERO
            }
        )

        for tutor_id in active:
            earnings = self.week_completions[
                (week, tutor_id)
            ]

            count = len(earnings)
            gross = (
                sum(earnings, ZERO)
                + self.week_noshow_charges[(week, tutor_id)]
            )

            if count < 10:
                commission_pct = dec("25")
            elif count < 25:
                commission_pct = dec("20")
            else:
                commission_pct = dec("15")

            commission = cash(
                gross * commission_pct / 100
            )

            penalties = self.week_penalties[
                (week, tutor_id)
            ]

            carried_in = self.carry[tutor_id]

            payable = (
                gross - commission
                - penalties + carried_in
            )

            if (
                payable > 0
                and self.annual[tutor_id] + payable
                > dec("30000")
            ):
                tds = cash(payable * dec("0.10"))
            else:
                tds = ZERO

            net = cash(payable - tds)

            if net >= dec("500"):
                paid = net
                carried_forward = ZERO
            else:
                paid = ZERO
                carried_forward = net

            self.carry[tutor_id] = carried_forward

            if paid:
                self.annual[tutor_id] += paid

            self.payouts.append({
                "week_start": str(week),
                "tutor_id": tutor_id,
                "completed_sessions": count,
                "gross": fmt(gross),
                "commission_pct": fmt(commission_pct),
                "commission": fmt(commission),
                "penalties": fmt(penalties),
                "tds": fmt(tds),
                "carried_in": fmt(carried_in),
                "net_paid": fmt(paid),
                "carried_forward": fmt(carried_forward)
            })

    # ---------- PROCESS ALL COMMANDS ----------

    def run(self):
        with (DATA / "commands.txt").open(
            encoding="utf-8-sig"
        ) as file:

            for line_no, raw in enumerate(file, 1):
                raw = raw.strip()

                if not raw or raw.startswith("#"):
                    continue

                parts = raw.split("|")
                command = parts[0]

                try:
                    if command == "REQUEST":
                        self.request(parts, line_no)

                    elif command == "CLOSE_WEEK":
                        self.close_week(
                            parts[2], parts[3]
                        )

                    else:
                        now = dt(parts[1])
                        request_id = parts[2]

                        if command == "CONFIRM":
                            self.confirm(
                                request_id, line_no
                            )

                        elif command == "CANCEL_STUDENT":
                            self.cancel_student(
                                request_id, now, line_no
                            )

                        elif command == "CANCEL_TUTOR":
                            self.cancel_tutor(
                                request_id, now, line_no
                            )

                        elif command == "RESCHEDULE":
                            self.reschedule(
                                request_id,
                                now,
                                parts[3],
                                line_no
                            )

                        elif command == "COMPLETE":
                            self.complete(
                                request_id, line_no
                            )

                        elif command == "RATE":
                            self.rate(
                                request_id,
                                int(parts[3]),
                                line_no
                            )

                        elif command == "NOSHOW_STUDENT":
                            session = self.sessions.get(
                                request_id
                            )

                            if (
                                session
                                and session["status"] == "CONFIRMED"
                                and now >= (
                                    session["start"]
                                    + timedelta(minutes=10)
                                )
                            ):
                                session["status"] = "NOSHOW_STUDENT"

                                self.week_noshow_charges[
                                    (
                                        week_start(session["start"]),
                                        session["tutor"]
                                    )
                                ] += session["price"]

                                self.log(
                                    line_no,
                                    request_id,
                                    command,
                                    "FULL_CHARGE",
                                    amount=session["price"]
                                )

                            else:
                                self.log(
                                    line_no,
                                    request_id,
                                    command,
                                    "INVALID_NOSHOW"
                                )

                        elif command == "NOSHOW_TUTOR":
                            session = self.sessions.get(
                                request_id
                            )

                            cancellation_time = (
                                session["start"]
                                if session else now
                            )

                            self.cancel_tutor(
                                request_id,
                                cancellation_time,
                                line_no,
                                command
                            )

                        else:
                            self.log(
                                line_no,
                                request_id,
                                command,
                                "UNKNOWN_COMMAND"
                            )

                except (
                    ValueError,
                    IndexError,
                    KeyError,
                    ArithmeticError
                ) as error:

                    print(
                        f"Warning: line {line_no} "
                        f"({command}): {error}"
                    )

                    if command == "REQUEST":
                        self.matches.append({
                            "request_id": (
                                parts[2]
                                if len(parts) > 2 else ""
                            ),
                            "status": "REJECTED",
                            "tutor_id": "",
                            "score": "",
                            "eligible_count": 0,
                            "surge_applied": "false",
                            "price": "0.00"
                        })

                    elif command != "CLOSE_WEEK":
                        self.log(
                            line_no,
                            parts[2] if len(parts) > 2 else "",
                            command,
                            "INVALID_INPUT"
                        )

        # ---------- GENERATE CSV FILES ----------

        write_csv(
            "match_decisions.csv",
            [
                "request_id",
                "status",
                "tutor_id",
                "score",
                "eligible_count",
                "surge_applied",
                "price"
            ],
            self.matches
        )

        write_csv(
            "session_ledger.csv",
            [
                "line_no",
                "request_id",
                "event",
                "tutor_id",
                "amount_to_student",
                "refund",
                "penalty",
                "reliability_after",
                "note"
            ],
            self.ledger
        )

        write_csv(
            "payouts.csv",
            [
                "week_start",
                "tutor_id",
                "completed_sessions",
                "gross",
                "commission_pct",
                "commission",
                "penalties",
                "tds",
                "carried_in",
                "net_paid",
                "carried_forward"
            ],
            self.payouts
        )

        print("Requests:", len(self.matches))
        print("Session events:", len(self.ledger))
        print("Payout rows:", len(self.payouts))
        print("Saved CSV files in:", OUT)


if __name__ == "__main__":
    Engine().run()
