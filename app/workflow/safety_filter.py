"""
Safety Filter — Validates AI-generated responses for hallucinations and unsafe content.

Prevents:
- Hallucinated commitments
- Fake scheduling promises
- Overpromising capabilities
- Unsafe automatic replies
- Privacy violations
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SafetySeverity(Enum):
    """Severity levels for safety violations."""

    SAFE = "safe"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class SafetyCheckResult:
    """Result of safety validation."""

    is_safe: bool
    severity: SafetySeverity
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    filtered_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "severity": self.severity.value,
            "violations": self.violations,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "filtered_text": self.filtered_text,
        }


class SafetyFilter:
    """Validates and filters AI-generated email responses."""

    # Patterns indicating potentially unsafe content
    DANGEROUS_PATTERNS = {
        "commitment_patterns": [
            r"i\s+(?:will|guarantee|promise|ensure|commit to)\s+(?:deliver|complete|finish|implement)\s+by\s+\d+\s+(?:hours?|days?|weeks?)",
            r"(?:we\s+can|i\s+can)\s+(?:deliver|complete)\s+this\s+(?:today|tomorrow|this\s+week)",
            r"we\s+(?:guarantee|promise|assure)\s+(?:\d+%?\s+)?(?:success|completion|delivery)",
        ],
        "scheduling_patterns": [
            r"(?:meeting|call|sync)\s+(?:scheduled|booked|confirmed)\s+for\s+(?:tomorrow|next|monday|tuesday|wednesday|thursday|friday)",
            r"i\s+(?:have|can)\s+(?:schedule|book)\s+(?:immediately|now|asap)",
        ],
        "overpromise_patterns": [
            r"(?:definitely|absolutely|certainly|100%)\s+(?:will|can)\s+(?:fix|solve|resolve)",
            r"(?:no|never)\s+(?:problem|issue|concern|doubt)",
        ],
        "legal_patterns": [
            r"(?:contract|agreement|legal|liable|liability|lawsuit)",
            r"(?:confidential|private|secret|proprietary)\s+(?:information|data|file)",
        ],
        "false_authority": [
            r"(?:on\s+behalf\s+of|as\s+(?:the|a)\s+(?:CEO|CTO|founder))",
            r"(?:i\s+am|i\'m)\s+(?:authorized|empowered|able)\s+to\s+(?:approve|sign|accept)\s+(?:the\s+)?(?:contract|agreement)",
        ],
    }

    # Restricted phrases that require human approval
    RESTRICTED_PHRASES = [
        "i'll call you",
        "let's schedule",
        "meeting set for",
        "confirmed for",
        "i can definitely",
        "we guarantee",
        "no problem",
        "contract",
        "legally",
        "liable",
    ]

    # Privacy patterns
    PRIVACY_PATTERNS = [
        r"\b(?:\d{3}[-.]?\d{3}[-.]?\d{4})\b",  # Phone numbers
        r"\b[\w\.-]+@[\w\.-]+\.\w+\b",  # Email addresses
        r"\b(?:\d{3}[-]?\d{2}[-]?\d{4})\b",  # SSN
        r"\b(?:credit\s+card|cc\s+(?:#|number)|cvv|ssn)\b",
    ]

    def __init__(self, strict_mode: bool = False):
        """
        Initialize safety filter.

        Args:
            strict_mode: If True, flag more content as requiring review
        """
        self.strict_mode = strict_mode
        self.violation_count = 0
        self.filter_count = 0

    def validate(
        self, text: str, sender: str = "", context: dict[str, Any] | None = None
    ) -> SafetyCheckResult:
        """
        Validate AI-generated response for safety issues.

        Args:
            text: Generated response text to validate
            sender: Email sender (for context)
            context: Additional context (email_category, urgency, etc.)

        Returns:
            SafetyCheckResult with validation details
        """
        result = SafetyCheckResult(is_safe=True, severity=SafetySeverity.SAFE)
        text_lower = text.lower()

        # Check for dangerous patterns
        for pattern_type, patterns in self.DANGEROUS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    result.violations.append(
                        f"Potential {pattern_type.replace('_', ' ')}: {pattern}"
                    )
                    result.is_safe = False
                    result.severity = SafetySeverity.CRITICAL

        # Check for restricted phrases
        for phrase in self.RESTRICTED_PHRASES:
            if phrase in text_lower:
                result.warnings.append(f"Contains restricted phrase: '{phrase}'")
                if self.strict_mode:
                    result.is_safe = False
                    result.severity = SafetySeverity.WARNING

        # Check for privacy concerns
        for pattern in self.PRIVACY_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                result.violations.append(f"Potential privacy concern detected: {pattern}")
                result.is_safe = False
                result.severity = SafetySeverity.CRITICAL

        # Check for generic "safe" patterns
        if not any(
            text_lower.count(phrase) > 0 for phrase in ["thank", "appreciate", "looking forward"]
        ):
            if self.strict_mode:
                result.warnings.append("Response lacks standard courtesy phrases")

        # Generate suggestions based on violations
        if result.violations or result.warnings:
            result.suggestions = self._generate_suggestions(
                result.violations, result.warnings, text
            )
            self.violation_count += 1

        return result

    def _generate_suggestions(
        self,
        violations: list[str],
        warnings: list[str],
        text: str,
    ) -> list[str]:
        """Generate human-friendly suggestions to fix safety issues."""
        suggestions = []

        if any("commitment" in v.lower() for v in violations):
            suggestions.append("Avoid making specific timeline commitments without verification")

        if any("scheduling" in v.lower() for v in violations):
            suggestions.append(
                "Use phrases like 'Let's discuss scheduling' instead of confirming dates"
            )

        if any("overpromise" in v.lower() for v in violations):
            suggestions.append("Replace absolute guarantees with 'I'll do my best to...'")

        if any("legal" in v.lower() for v in violations):
            suggestions.append("Legal matters should be reviewed by appropriate teams")

        if any("false authority" in v.lower() for v in violations):
            suggestions.append("Ensure you have proper authority before making claims")

        if any("privacy" in v.lower() for v in violations):
            suggestions.append("Remove sensitive information (SSN, phone, card numbers)")

        if "'let's schedule'" in warnings or "'meeting set for'" in warnings:
            suggestions.append("Replace specific scheduling with 'I'll follow up to schedule'")

        if not suggestions:
            suggestions.append("Review response with appropriate team member before sending")

        return suggestions[:3]  # Return top 3 suggestions

    def filter_and_warn(self, text: str, sender: str = "") -> tuple[str, list[str]]:
        """
        Filter text and return warnings without modifying content.

        Returns:
            (original_text, list_of_warnings)
        """
        result = self.validate(text, sender)
        warnings = result.violations + result.warnings
        self.filter_count += 1
        return text, warnings

    def should_require_approval(self, result: SafetyCheckResult) -> bool:
        """Determine if response requires human approval before sending."""
        if result.severity == SafetySeverity.CRITICAL:
            return True
        if result.severity == SafetySeverity.WARNING and self.strict_mode:
            return True
        return bool(result.violations)

    def get_stats(self) -> dict[str, Any]:
        """Get filter statistics."""
        return {
            "violations_detected": self.violation_count,
            "responses_filtered": self.filter_count,
            "strict_mode": self.strict_mode,
        }
