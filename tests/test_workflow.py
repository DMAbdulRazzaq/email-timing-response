import os
import sys

from app.workflow.feedback import reward_from_correction
from app.workflow.priority_engine import score_email
from app.workflow.schemas import EmailRecord

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_recruiter_deadline_scores_urgent():
    email = EmailRecord(
        id="m1",
        thread_id="t1",
        sender="recruiter@company.com",
        subject="Interview schedule deadline tomorrow",
        body="Please confirm your interview slot today.",
    )

    scored = score_email(email, follow_up_count=1)

    assert scored.priority >= 85
    assert scored.category == "URGENT"
    assert any("hiring" in reason.lower() for reason in scored.reasons)


def test_marketing_sender_scores_low():
    email = EmailRecord(
        id="m2",
        thread_id="t2",
        sender="marketing@canva.com",
        subject="Limited discount promotion",
        body="Click now for a sale and unsubscribe here.",
    )

    scored = score_email(email)

    assert scored.priority <= 10
    assert scored.category == "SPAM"


def test_feedback_reward_penalizes_bad_archive():
    reward = reward_from_correction("archive", "reply_now")

    assert reward < 0


def test_feedback_reward_positive_for_matching_action():
    reward = reward_from_correction("mark_important", "mark_important")

    assert reward > 0
