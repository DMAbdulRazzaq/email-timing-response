"""
Response Generator — AI-powered draft reply generation with Gemini.

Provides context-aware, tone-aware email response drafting with:
- Gemini API integration
- Thread-aware generation
- Tone selection
- Personalization learning
- Safety validation
"""

import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.workflow.schemas import EmailRecord, ThreadContext


@dataclass
class GeneratedResponse:
    """Result of AI response generation."""

    message_id: str
    thread_id: str
    original_sender: str
    generated_text: str
    tone_used: str
    model_used: str
    confidence: float
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    warnings: list[str] = field(default_factory=list)
    persona_applied: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResponseGenerator:
    """Generates AI-powered email reply drafts with Gemini."""

    SUPPORTED_TONES = [
        "professional",
        "friendly",
        "formal",
        "concise",
        "enthusiastic",
        "apologetic",
    ]

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        self.call_count = 0
        self.total_tokens = 0

    def generate(
        self,
        email: EmailRecord,
        tone: str = "professional",
        thread: ThreadContext | None = None,
        personalization: dict[str, Any] | None = None,
        max_length: int = 500,
    ) -> GeneratedResponse:
        """
        Generate an AI reply draft.

        Args:
            email: The email to reply to
            tone: Desired tone (professional|friendly|formal|concise|enthusiastic|apologetic)
            thread: Thread context for conversation awareness
            personalization: User preferences (preferred_length, style, etc.)
            max_length: Maximum response length in characters

        Returns:
            GeneratedResponse with generated text and metadata
        """
        if tone not in self.SUPPORTED_TONES:
            tone = "professional"

        if not self.api_key:
            return self._fallback_response(email, tone)

        prompt = self._build_generation_prompt(email, tone, thread, personalization, max_length)

        try:
            response_text = self._call_gemini(prompt)
            parsed = self._parse_generation_response(response_text)

            return GeneratedResponse(
                message_id=email.id,
                thread_id=email.thread_id,
                original_sender=email.sender,
                generated_text=parsed.get("reply_text", ""),
                tone_used=tone,
                model_used=self.model,
                confidence=float(parsed.get("confidence", 0.7)),
                warnings=parsed.get("warnings", []),
                persona_applied=parsed.get("persona_applied", "default"),
            )
        except (json.JSONDecodeError, urllib.error.URLError, TimeoutError) as e:
            return self._fallback_response(email, tone, error=str(e))

    def regenerate_with_tone(
        self,
        response: GeneratedResponse,
        new_tone: str,
        personalization: dict[str, Any] | None = None,
    ) -> GeneratedResponse:
        """
        Regenerate a response with a different tone.

        Args:
            response: Original GeneratedResponse
            new_tone: New tone to apply
            personalization: User preferences

        Returns:
            New GeneratedResponse with different tone
        """
        if new_tone not in self.SUPPORTED_TONES:
            new_tone = "professional"

        email = EmailRecord(
            id=response.message_id,
            thread_id=response.thread_id,
            sender=response.original_sender,
            subject="",
            body="",
        )

        return self.generate(email, new_tone, personalization=personalization)

    def _build_generation_prompt(
        self,
        email: EmailRecord,
        tone: str,
        thread: ThreadContext | None,
        personalization: dict[str, Any] | None,
        max_length: int,
    ) -> str:
        """Build structured prompt for Gemini."""

        thread_info = ""
        if thread:
            thread_info = f"""
Thread Context:
- Total messages: {thread.message_count}
- Follow-up count: {thread.follow_up_count}
- Latest sender: {thread.latest_sender}
- Previous subjects: {', '.join(thread.previous_subjects[-3:])}
- Summary: {thread.summary}
"""

        persona_hints = ""
        if personalization:
            if personalization.get("preferred_length"):
                persona_hints += f"- Preferred length: {personalization['preferred_length']}\n"
            if personalization.get("reply_style"):
                persona_hints += f"- Reply style: {personalization['reply_style']}\n"
            if personalization.get("signature"):
                persona_hints += f"- Signature: {personalization['signature']}\n"

        tone_desc = self._get_tone_description(tone)

        return f"""
You are an intelligent email assistant helping compose professional, context-aware replies.

INCOMING EMAIL:
From: {email.sender}
Subject: {email.subject}
Body: {email.body}

{thread_info}

TONE GUIDELINES ({tone}):
{tone_desc}

PERSONALIZATION:
{persona_hints if persona_hints else "- Use default professional style"}

TASK:
Generate a professional email reply that:
1. Acknowledges the sender's message
2. Addresses all key points raised
3. Maintains the specified tone
4. Stays within {max_length} characters
5. Sounds human and authentic
6. Avoids making commitments or promises you cannot keep
7. Is appropriate for business communication

Return ONLY valid JSON with no markdown formatting:
{{
  "reply_text": "the generated reply text here",
  "confidence": 0.85,
  "persona_applied": "professional",
  "warnings": [],
  "reasoning": "why this reply was generated this way"
}}
""".strip()

    def _get_tone_description(self, tone: str) -> str:
        """Get detailed guidance for specific tone."""
        descriptions = {
            "professional": "Formal, business-appropriate. Use clear sentences. Maintain distance. Focus on facts.",
            "friendly": "Warm but professional. Use conversational language. Show genuine interest. Be approachable.",
            "formal": "Very formal. Use titles, proper grammar. Minimize contractions. Highly structured.",
            "concise": "Brief and to-the-point. Bullet points acceptable. Remove fluff. Direct communication.",
            "enthusiastic": "Positive and energetic. Show genuine interest. Use exclamation points sparingly. Engaged tone.",
            "apologetic": "Acknowledge issues. Show understanding. Provide solutions. Rebuild trust. Take responsibility.",
        }
        return descriptions.get(tone, descriptions["professional"])

    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API and return response text."""
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "responseMimeType": "application/json",
                "maxOutputTokens": 1000,
            },
        }

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        self.call_count += 1
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text

    def _parse_generation_response(self, response_text: str) -> dict[str, Any]:
        """Parse Gemini's JSON response."""
        try:
            parsed = json.loads(response_text)
            return {
                "reply_text": parsed.get("reply_text", "").strip(),
                "confidence": float(parsed.get("confidence", 0.7)),
                "persona_applied": parsed.get("persona_applied", "default"),
                "warnings": parsed.get("warnings", []),
                "reasoning": parsed.get("reasoning", ""),
            }
        except (json.JSONDecodeError, ValueError):
            return {
                "reply_text": response_text[:500],
                "confidence": 0.5,
                "persona_applied": "fallback",
                "warnings": ["Failed to parse structured response"],
                "reasoning": "Returned raw text due to parsing failure",
            }

    def _fallback_response(
        self,
        email: EmailRecord,
        tone: str,
        error: str = "",
    ) -> GeneratedResponse:
        """Provide fallback response when API unavailable."""
        fallback_templates = {
            "professional": f"Hi {email.sender.split()[0] if email.sender else 'there'},\n\nThank you for your email regarding {email.subject[:30]}. I appreciate you reaching out.\n\nBest regards",
            "friendly": f"Hi {email.sender.split()[0] if email.sender else 'there'}!\n\nThanks for reaching out about {email.subject[:30]}. I really appreciate it!\n\nTalk soon!",
            "formal": f"Dear {email.sender},\n\nThank you for your communication regarding {email.subject[:30]}. Your message has been received and acknowledged.\n\nRespectfully",
            "concise": f"Hi,\n\nThanks for the message. Noted.\n\nBest",
            "enthusiastic": f"Hey {email.sender.split()[0] if email.sender else 'there'}!\n\nLove the {email.subject[:20]}! Excited to dive into this!\n\nCheers!",
            "apologetic": f"Hi {email.sender.split()[0] if email.sender else 'there'},\n\nI sincerely apologize for any inconvenience. I'm committed to making this right.\n\nBest regards",
        }

        warning = "API unavailable - using template fallback"
        if error:
            warning += f": {error}"

        return GeneratedResponse(
            message_id=email.id,
            thread_id=email.thread_id,
            original_sender=email.sender,
            generated_text=fallback_templates.get(tone, fallback_templates["professional"]),
            tone_used=tone,
            model_used="fallback-template",
            confidence=0.4,
            warnings=[warning],
            persona_applied="fallback",
        )
