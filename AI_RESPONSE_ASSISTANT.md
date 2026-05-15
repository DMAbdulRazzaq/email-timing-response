"""
AI Response Assistant — Integration Guide and Architecture

This module provides production-grade AI email response generation with:
- Gemini-powered draft generation
- Tone selection and regeneration
- Safety validation
- User personalization learning
- RL feedback integration
- Gmail draft management
"""

# ── QUICK START ──────────────────────────────────────────────────────────────

## 1. REST API ENDPOINTS (FastAPI)

All endpoints are available at `http://localhost:8000/api/v1/responses/`

### Generate Response Draft
```
POST /api/v1/responses/generate
Content-Type: application/json

{
    "message_id": "thread_id_xyz",
    "thread_id": "thread_id_xyz",
    "sender": "recruiter@company.com",
    "subject": "Opportunity at TechCorp",
    "body": "We have an exciting role for you...",
    "tone": "professional",
    "max_length": 500,
    "require_approval": true
}

Response:
{
    "success": true,
    "response_id": "resp_abc123",
    "generated_text": "Dear Recruiter...",
    "tone_used": "professional",
    "confidence": 0.87,
    "warnings": [],
    "requires_approval": false,
    "safety": {
        "is_safe": true,
        "severity": "safe",
        "violations": [],
        "warnings": [],
        "suggestions": []
    }
}
```

### Regenerate with Different Tone
```
POST /api/v1/responses/regenerate
{
    "response_id": "resp_abc123",
    "new_tone": "friendly"
}
```

### Record User Feedback
```
POST /api/v1/responses/feedback
{
    "response_id": "resp_abc123",
    "feedback_type": "approved",  // or "edited" or "rejected"
    "edited_text": "Dear Recruiter, thank you for...",
    "approval_time_seconds": 5.2,
    "feedback_notes": "Good tone, minor edit for clarity"
}
```

### Get Supported Tones
```
GET /api/v1/responses/tones
```

### Get User Profile & Statistics
```
GET /api/v1/responses/personalization
GET /api/v1/responses/stats
```

---

## 2. FLASK UI INTEGRATION

### Simple HTML Integration
```html
<!-- Include the AI reply panel component -->
<script src="/static/ai_reply_panel.js"></script>
<link rel="stylesheet" href="/static/ai_reply_panel.css">

<!-- In email card: -->
<button onclick="showAIReplyPanel(emailData)">
    Generate AI Reply
</button>

<!-- Panel appears automatically -->
```

### Usage Flow
1. User clicks "Generate AI Reply"
2. AI panel opens with generated draft
3. User selects tone (optional)
4. User can edit, approve, or reject
5. Feedback recorded for learning
6. Draft sent to Gmail (with human approval)

---

## 3. PYTHON API USAGE

### Generate Response
```python
from app.workflow.response_generator import ResponseGenerator
from app.workflow.schemas import EmailRecord

generator = ResponseGenerator()

email = EmailRecord(
    id="msg123",
    thread_id="thread123",
    sender="boss@company.com",
    subject="Q1 Review Meeting",
    body="Let's discuss your performance...",
)

# Generate professional response
response = generator.generate(
    email=email,
    tone="professional",
    max_length=300,
)

print(response.generated_text)
print(f"Confidence: {response.confidence}")
```

### Validate Response for Safety
```python
from app.workflow.safety_filter import SafetyFilter

filter = SafetyFilter(strict_mode=False)

result = filter.validate(
    response.generated_text,
    sender="boss@company.com",
)

if not result.is_safe:
    print("Safety violations:", result.violations)
    print("Suggestions:", result.suggestions)
```

### Track Personalization
```python
from app.workflow.personalization_memory import PersonalizationMemory

memory = PersonalizationMemory()

# Record user action
memory.record_action(
    response_id="resp123",
    sender="recruiter@company.com",
    action="approved",
    tone="friendly",
    generated_text="...",
)

# Get recommendations for sender
recommended_tone = memory.recommend_tone_for_sender("recruiter@company.com")
print(f"Recommended tone: {recommended_tone}")

# Get user profile
profile = memory.get_personalization_hints()
print(f"Preferred length: {profile['preferred_length']}")
```

### Track RL Feedback
```python
from app.workflow.response_feedback import ResponseFeedbackTracker

tracker = ResponseFeedbackTracker()

# Record feedback
feedback = tracker.record_feedback(
    response_id="resp123",
    sender="recruiter@company.com",
    original_action="reply_now",
    generated_tone="professional",
    feedback_type="approved",
    approval_time_seconds=3.2,
)

# Get statistics
stats = tracker.get_session_stats()
print(f"Approval rate: {stats['approval_rate']:.2%}")

# Export for RL training
training_data = tracker.export_rl_training_data()
```

---

## 4. SUPPORTED TONES

| Tone | Description | Best For |
|------|-------------|----------|
| **professional** | Formal, business-appropriate | Default for work emails |
| **friendly** | Warm but professional | Casual colleagues, initial contact |
| **formal** | Very formal, highly structured | Legal, executive, formal matters |
| **concise** | Brief and to-the-point | Time-sensitive, urgent matters |
| **enthusiastic** | Positive and energetic | Sales, partnerships, exciting news |
| **apologetic** | Acknowledges issues | Complaints, delays, mistakes |

---

## 5. SAFETY VALIDATION

Safety filter prevents:
- Hallucinated commitments ("I guarantee delivery by Friday")
- Fake scheduling ("Meeting scheduled for 3pm")
- Overpromising ("No problem, definitely will work")
- Privacy violations (phone numbers, SSN)
- False authority claims ("As CEO, I approve...")

### Severity Levels
- **SAFE**: No violations, ready to send
- **WARNING**: Minor concerns, human review recommended
- **CRITICAL**: Cannot send without review

---

## 6. PERSONALIZATION LEARNING

The system learns:
1. **Sender preferences** - What tone works best for specific people
2. **Length preferences** - Does user prefer concise or detailed replies?
3. **Style patterns** - Formal vs casual, technical vs simple
4. **Effectiveness** - Which tones get approved vs rejected

### Feedback Signals
- **Approved** → +10 reward (strong positive)
- **Edited** → +2 reward (partial positive, learning opportunity)
- **Rejected** → -5 reward (negative, needs improvement)

---

## 7. INTEGRATION WITH RL AGENT

Response feedback integrates with DQN training:

```python
# User feedback becomes RL reward
feedback = tracker.record_feedback(
    response_id="resp123",
    feedback_type="approved",  # User liked it
)

# Reward signal: +10.0
# This reward can feed back into DQN training

# Track which tones work best
tone_performance = tracker.get_tone_performance()
# Returns approval_rate, avg_reward for each tone

# Adapt generation based on effectiveness
if tone_performance["friendly"]["approval_rate"] > 0.8:
    default_tone = "friendly"
```

---

## 8. DEPLOYMENT CHECKLIST

- [ ] Set GEMINI_API_KEY environment variable
- [ ] Ensure Gmail API credentials are configured
- [ ] Create data directories: `data/draft_interactions.jsonl`, `data/response_feedback.jsonl`
- [ ] Run tests: `pytest tests/test_response_generation.py`
- [ ] Test API: `curl http://localhost:8000/api/v1/responses/health`
- [ ] Monitor: Check `/api/v1/responses/stats` for usage

---

## 9. EXAMPLE WORKFLOW

```python
# Complete workflow example
import asyncio
from app.workflow.response_generator import ResponseGenerator
from app.workflow.safety_filter import SafetyFilter
from app.workflow.personalization_memory import PersonalizationMemory
from app.workflow.response_feedback import ResponseFeedbackTracker
from app.workflow.schemas import EmailRecord

async def process_email_reply(email_data):
    """Complete AI response workflow."""
    
    # Initialize components
    generator = ResponseGenerator()
    safety_filter = SafetyFilter(strict_mode=False)
    personalization = PersonalizationMemory()
    feedback_tracker = ResponseFeedbackTracker()
    
    # Parse email
    email = EmailRecord(**email_data)
    
    # Get personalization hints
    hints = personalization.get_personalization_hints()
    recommended_tone = personalization.recommend_tone_for_sender(email.sender)
    
    # Generate response
    response = generator.generate(
        email=email,
        tone=recommended_tone,
        personalization=hints,
    )
    
    # Validate safety
    safety_result = safety_filter.validate(
        response.generated_text,
        sender=email.sender,
    )
    
    # Require human approval if unsafe
    if not safety_result.is_safe:
        return {
            "status": "requires_review",
            "response": response,
            "safety_issues": safety_result.violations,
            "suggestions": safety_result.suggestions,
        }
    
    # Create draft
    # draft = create_ai_draft(service, email.sender, email.subject, response.generated_text, ...)
    
    # Wait for user feedback (via API)
    # When feedback comes in...
    feedback = feedback_tracker.record_feedback(
        response_id=response.message_id,
        sender=email.sender,
        original_action="reply_now",
        generated_tone=recommended_tone,
        feedback_type="approved",  # User approved
    )
    
    # Update personalization
    personalization.record_action(
        response_id=response.message_id,
        sender=email.sender,
        action="approved",
        tone=recommended_tone,
        generated_text=response.generated_text,
    )
    
    return {
        "status": "success",
        "reward": feedback.reward_signal,
        "response": response,
    }

# Usage
if __name__ == "__main__":
    email_data = {
        "id": "msg123",
        "thread_id": "thread123",
        "sender": "recruiter@techcorp.com",
        "subject": "Software Engineer Role",
        "body": "We'd love to hear about your experience...",
    }
    
    result = asyncio.run(process_email_reply(email_data))
    print(result)
```

---

## 10. FILE STRUCTURE

```
app/
├── workflow/
│   ├── response_generator.py      # Core AI generation
│   ├── safety_filter.py           # Safety validation
│   ├── personalization_memory.py  # User learning
│   ├── response_feedback.py       # RL reward tracking
│   └── gmail_actions.py           # Extended with draft management
│
├── api/
│   ├── __init__.py
│   └── response_routes.py         # FastAPI routes
│
ui/
├── web_ui.py                      # Flask routes
└── templates/
    ├── index.html                 # Main UI
    └── ai_reply_panel.html        # AI component
    
data/
├── draft_interactions.jsonl       # User feedback storage
└── response_feedback.jsonl        # RL reward tracking
```

---

## 11. TESTING

```bash
# Test response generation
pytest tests/test_response_generation.py -v

# Test safety filter
pytest tests/test_safety_filter.py -v

# Test API endpoints
pytest tests/test_response_routes.py -v

# Full integration test
pytest tests/test_ai_response_integration.py -v
```

---

## 12. TROUBLESHOOTING

**Issue**: "Error: API unavailable - using template fallback"
- Check GEMINI_API_KEY is set
- Verify API key has Generative Language API enabled
- Check network connectivity

**Issue**: Safety warnings for legitimate responses
- Set `strict_mode=False` in SafetyFilter
- Add context to safety_filter.validate() call
- Review and update DANGEROUS_PATTERNS if needed

**Issue**: Low approval rates
- Check tone effectiveness with `tone_performance`
- Review user feedback and edit patterns
- Adjust personalization hints

**Issue**: Memory/personalization not persisting
- Verify data directory is writable
- Check JSON storage file paths
- Ensure JSONL files are properly formatted

---

## 13. MONITORING & METRICS

Track these metrics:
- **Generation success rate**: % of responses generated without errors
- **Safety filtering rate**: % of responses flagged by safety checks  
- **Approval rate**: % of generated drafts approved by users
- **Tone effectiveness**: Approval rate by tone type
- **Personalization confidence**: How well recommendations match user preference
- **Response time**: Latency of generation endpoint

Monitor via `/api/v1/responses/stats` endpoint

---

## 14. FUTURE ENHANCEMENTS

- [ ] Multi-language support
- [ ] Email attachment handling
- [ ] Template-based generation
- [ ] Batch processing
- [ ] Analytics dashboard
- [ ] A/B testing framework
- [ ] Custom safety rules per user
- [ ] Handwriting-style personalization
- [ ] Sentiment analysis feedback
- [ ] Calendar-aware scheduling suggestions
"""
