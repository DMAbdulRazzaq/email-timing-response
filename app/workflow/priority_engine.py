from app.workflow.schemas import EmailRecord

IGNORE_SENDERS = ["canva", "newsletter", "marketing", "noreply"]
HIRING_KEYWORDS = ["interview", "recruiter", "hiring", "job", "internship", "offer"]
DEADLINE_KEYWORDS = ["deadline", "due", "last date", "expires", "today", "tomorrow", "urgent"]
ACTION_KEYWORDS = ["reply", "respond", "confirm", "schedule", "submit", "action required"]
TRUSTED_SENDERS = [".edu", "university", "professor", "recruiter", "hr@", "careers"]
PROMOTION_KEYWORDS = ["sale", "discount", "unsubscribe", "promotion", "deal", "offer ends"]


def should_ignore_sender(sender: str) -> bool:
    return any(word in sender.lower() for word in IGNORE_SENDERS)


def score_email(email: EmailRecord, follow_up_count: int = 0) -> EmailRecord:
    sender_lower = email.sender.lower()
    text = f"{email.sender} {email.subject} {email.body}".lower()
    score = 40
    reasons = []

    if any(keyword in text for keyword in HIRING_KEYWORDS):
        score += 30
        reasons.append("Contains hiring or career keyword")
    if any(keyword in text for keyword in DEADLINE_KEYWORDS):
        score += 25
        reasons.append("Deadline or urgency detected")
    if any(keyword in text for keyword in ACTION_KEYWORDS):
        score += 20
        reasons.append("Action required")
    if any(keyword in sender_lower for keyword in TRUSTED_SENDERS):
        score += 15
        reasons.append("Sender appears trusted")
    if follow_up_count:
        score += min(20, follow_up_count * 8)
        reasons.append(f"Thread has {follow_up_count} follow-up signal(s)")
    if any(keyword in text for keyword in PROMOTION_KEYWORDS):
        score -= 35
        reasons.append("Promotional language detected")
    if should_ignore_sender(email.sender):
        score = min(score, 10)
        reasons.append("Sender matches ignored newsletter or marketing source")

    email.priority = max(0, min(100, score))
    email.category = _category(email.priority)
    email.reasons = reasons or ["No strong priority signals detected"]
    return email


def _category(score: int) -> str:
    if score >= 85:
        return "URGENT"
    if score >= 65:
        return "IMPORTANT"
    if score >= 35:
        return "NORMAL"
    if score >= 15:
        return "PROMOTION"
    return "SPAM"
