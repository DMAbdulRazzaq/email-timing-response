"""Generate a sample AI response using the existing ResponseGenerator.

This script uses fallback templates if the Gemini API key is not set.

Usage:
    python experiments/generate_sample_response.py
"""

import json
from pathlib import Path
from types import SimpleNamespace

from app.workflow.response_generator import ResponseGenerator


def main():
    rg = ResponseGenerator()
    # Prefer constructing a real Email dataclass if available;
    # fallback to SimpleNamespace otherwise.
    try:
        import importlib

        email_module = importlib.import_module("data.email_data")
        Email = getattr(email_module, "Email")
        email = Email(
            subject="Job Opportunity: Senior ML Engineer",
            sender="recruiter@company.com",
            priority=2,
            sender_importance=2,
            waiting_time=10,
            workload=1,
            time_of_day=10,
        )
        setattr(email, "id", "sample123")
        setattr(email, "message_id", "sample123")
        setattr(email, "thread_id", "thread_sample")
        print("Using data.email_data.Email for sample (if numpy available)")
    except Exception:
        email = SimpleNamespace(
            id="sample123",
            message_id="sample123",
            thread_id="thread_sample",
            sender="recruiter@company.com",
            subject="Job Opportunity: Senior ML Engineer",
            body=(
                "Hi,\n\nWe have a great role for a Senior ML Engineer "
                "focused on MLOps and email automation. "
                "Would you be interested in a quick call to discuss?\n\n"
                "Best,\nRecruiter"
            ),
        )
        print("Falling back to SimpleNamespace for sample email " "(numpy or Email import missing)")

    resp = rg.generate(
        email,
        tone="professional",
        thread=None,
        personalization={},
        max_length=512,
    )

    out = {
        "message_id": getattr(resp, "message_id", email.message_id),
        "generated_text": getattr(resp, "generated_text", str(resp)),
        "tone_used": getattr(resp, "tone_used", "professional"),
        "confidence": getattr(resp, "confidence", None),
        "warnings": getattr(resp, "warnings", None),
    }

    out_path = Path("data/experiments/sample_ai_response.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print("Wrote sample AI response to", out_path)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
