import json
import os
import urllib.error
import urllib.request

from app.workflow.schemas import EmailRecord, IntelligenceResult, ThreadContext


class GeminiContextEngine:
    """Gemini adapter with a deterministic fallback for local demos and tests."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

    def analyze(
        self, email: EmailRecord, thread: ThreadContext | None = None
    ) -> IntelligenceResult:
        if not self.api_key:
            return self._fallback(email, thread)

        prompt = self._build_prompt(email, thread)
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
        }

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(text)
            return IntelligenceResult(
                summary=parsed.get("summary", ""),
                tone=parsed.get("tone", "neutral"),
                urgency_reasoning=parsed.get("urgency_reasoning", ""),
                suggested_reply=parsed.get("suggested_reply", ""),
                recommended_action=parsed.get("recommended_action", "delay_reply"),
                confidence=float(parsed.get("confidence", 0.5)),
                risks=parsed.get("risks", []),
            )
        except (KeyError, json.JSONDecodeError, urllib.error.URLError, TimeoutError):
            return self._fallback(email, thread)

    def _build_prompt(self, email: EmailRecord, thread: ThreadContext | None) -> str:
        thread_context = thread.to_dict() if thread else {}
        return f"""
You are an email workflow intelligence engine. Return only valid JSON.

Allowed recommended_action values:
reply_now, delay_reply, mark_important, archive

Analyze this email for a human-in-the-loop Gmail automation system.

Email:
{json.dumps(email.to_dict(), ensure_ascii=False)}

Thread context:
{json.dumps(thread_context, ensure_ascii=False)}

Required JSON schema:
{{
  "summary": "one sentence",
  "tone": "professional|urgent|casual|promotional|angry|neutral",
  "urgency_reasoning": "why this should or should not be handled soon",
  "suggested_reply": "draft reply, empty if no reply is needed",
  "recommended_action": "reply_now|delay_reply|mark_important|archive",
  "confidence": 0.0,
  "risks": ["privacy or automation risks"]
}}
""".strip()

    def _fallback(self, email: EmailRecord, thread: ThreadContext | None) -> IntelligenceResult:
        if email.priority >= 85:
            action = "reply_now"
        elif email.priority >= 65:
            action = "mark_important"
        elif email.category in {"PROMOTION", "SPAM"}:
            action = "archive"
        else:
            action = "delay_reply"

        follow_up_text = ""
        if thread and thread.follow_up_count:
            follow_up_text = f" Thread contains {thread.follow_up_count} follow-up signal(s)."

        return IntelligenceResult(
            summary=email.body[:180] or email.subject,
            tone="neutral",
            urgency_reasoning="Rule-based fallback from priority score." + follow_up_text,
            suggested_reply="",
            recommended_action=action,
            confidence=min(0.95, max(0.35, email.priority / 100)),
            risks=["Gemini API key not configured; used deterministic fallback"],
        )
