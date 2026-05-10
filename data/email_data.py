from dataclasses import dataclass
import numpy as np


@dataclass
class Email:
    subject: str
    sender: str
    priority: int  # 1=low  2=medium  3=high
    sender_importance: int  # 1=promo  2=normal  3=academic/gov
    waiting_time: int  # minutes
    workload: int  # 1=light  2=moderate  3=heavy
    time_of_day: int  # 0-23

    def to_state_vector(self) -> np.ndarray:
        """
        Normalized [0,1] — identical to to_state() in ONE_CELL_TRAIN.py.
        Must never change or loaded weights will give wrong actions.
        """
        return np.array(
            [
                (self.priority - 1) / 2.0,
                (self.sender_importance - 1) / 2.0,
                min(self.waiting_time, 1440) / 1440.0,
                (self.workload - 1) / 2.0,
                self.time_of_day / 23.0,
            ],
            dtype=np.float32,
        )


# =========================
# Synthetic Email Metadata
# =========================

PRIORITY_MAP = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


SENDER_POOLS = {
    "high": [
        "professor@bmsce.ac.in",
        "hod@college.edu",
        "gov@karnataka.gov.in",
        "manager@company.com",
    ],
    "medium": [
        "friend@gmail.com",
        "teammate@project.com",
        "club@college.edu",
        "hr@startup.com",
    ],
    "low": [
        "promo@shopping.com",
        "newsletter@offers.com",
        "ads@marketing.com",
        "spam@random.net",
    ],
}


SUBJECT_POOLS = {
    "high": [
        "Urgent Project Deadline",
        "Exam Schedule Released",
        "Government Document Required",
        "Meeting at 10 AM",
    ],
    "medium": [
        "Project Update",
        "Team Discussion",
        "Weekend Plan",
        "Assignment Reminder",
    ],
    "low": [
        "50% Discount Offer",
        "Buy One Get One Free",
        "Weekly Newsletter",
        "Special Promotion",
    ],
}
