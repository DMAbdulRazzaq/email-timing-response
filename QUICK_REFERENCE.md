# AI Response Assistant — Quick Reference

## Files Overview

### Core Components

#### 1. Response Generator
**File**: `app/workflow/response_generator.py`
**Purpose**: Generate AI email responses using Gemini

```python
from app.workflow.response_generator import ResponseGenerator
from app.workflow.schemas import EmailRecord

generator = ResponseGenerator()  # Auto-loads GEMINI_API_KEY

email = EmailRecord(
    id="msg123",
    thread_id="thread123",
    sender="boss@company.com",
    subject="Meeting",
    body="Can you join?",
)

response = generator.generate(
    email=email,
    tone="professional",
    max_length=300,
)

print(response.generated_text)
print(response.confidence)
```

---

#### 2. Safety Filter  
**File**: `app/workflow/safety_filter.py`
**Purpose**: Validate responses for safety issues

```python
from app.workflow.safety_filter import SafetyFilter

filter = SafetyFilter(strict_mode=False)

result = filter.validate(
    "I guarantee delivery by Friday",
    sender="client@company.com",
)

if not result.is_safe:
    print(result.violations)      # What's wrong
    print(result.suggestions)     # How to fix
```

---

#### 3. Personalization Memory
**File**: `app/workflow/personalization_memory.py`
**Purpose**: Learn user preferences

```python
from app.workflow.personalization_memory import PersonalizationMemory

memory = PersonalizationMemory()

# Record when user approves a response
memory.record_action(
    response_id="resp123",
    sender="recruiter@company.com",
    action="approved",
    tone="friendly",
    generated_text="...",
)

# Get recommendations
tone = memory.recommend_tone_for_sender("recruiter@company.com")
hints = memory.get_personalization_hints()
```

---

#### 4. Response Feedback
**File**: `app/workflow/response_feedback.py`
**Purpose**: Track feedback and generate RL rewards

```python
from app.workflow.response_feedback import ResponseFeedbackTracker

tracker = ResponseFeedbackTracker()

# Record user feedback
feedback = tracker.record_feedback(
    response_id="resp123",
    sender="recruiter@company.com",
    original_action="reply_now",
    generated_tone="professional",
    feedback_type="approved",  # +10 reward
)

# Get statistics
stats = tracker.get_session_stats()
print(f"Approval rate: {stats['approval_rate']:.1%}")
```

---

#### 5. Gmail Actions (Extended)
**File**: `app/workflow/gmail_actions.py`
**Purpose**: Create, manage, send Gmail drafts

```python
from app.workflow.gmail_actions import (
    create_ai_draft,
    update_draft,
    send_draft,
    get_draft_preview,
)

# Create draft from AI response
draft = create_ai_draft(
    service=gmail_service,
    to_address="recipient@company.com",
    subject="Re: Meeting",
    body_text="Yes, I can attend.",
    thread_id="thread123",
    labels=["AI/Draft"],
)

# Preview before sending
preview = get_draft_preview(service, draft['id'])
print(preview['snippet'])

# Send if approved
send_draft(service, draft['id'])
```

---

### API Layer

#### FastAPI Routes
**File**: `app/api/response_routes.py`
**Base Path**: `/api/v1/responses/`

```python
# Routes available:
POST   /generate           # Generate response
POST   /regenerate         # Try different tone
POST   /feedback          # Record user feedback
GET    /tones             # List supported tones
GET    /personalization   # Get user profile
GET    /stats             # Get metrics
GET    /health            # Health check
```

---

#### Flask Routes  
**File**: `ui/web_ui.py`
**Base Path**: `/api/responses/`

```python
# Routes available:
POST   /generate           # Via Flask
POST   /regenerate         # Via Flask
POST   /feedback          # Via Flask
GET    /tones             # Get tone list
GET    /personalization   # Get profile
GET    /stats             # Get stats
```

---

### UI Components

#### AI Reply Panel
**File**: `ui/templates/ai_reply_panel.html`

Include in your HTML:
```html
<script src="/static/ai_reply_panel.js"></script>
<link rel="stylesheet" href="/static/ai_reply_panel.css">

<!-- Trigger the panel -->
<button onclick="showAIReplyPanel(emailData)">
    Generate AI Reply
</button>
```

---

## Supported Tones

```
professional  → Default, business-appropriate
friendly      → Warm, conversational
formal        → Very structured, formal
concise       → Brief, direct
enthusiastic  → Positive, energetic
apologetic    → Acknowledges issues
```

---

## Data Storage

### Personalization Memory
**File**: `data/draft_interactions.jsonl`
```json
{
  "response_id": "resp123",
  "sender": "recruiter@company.com",
  "action": "approved",
  "original_tone": "friendly",
  "generated_text": "...",
  "user_action_text": "...",
  "edit_distance": 45,
  "timestamp": "2026-05-14T10:30:00Z",
  "feedback_notes": "Good tone"
}
```

### Response Feedback
**File**: `data/response_feedback.jsonl`
```json
{
  "response_id": "resp123",
  "sender": "recruiter@company.com",
  "original_action": "reply_now",
  "generated_tone": "professional",
  "user_feedback_type": "approved",
  "reward_signal": 10.0,
  "safety_passed": true,
  "timestamp": "2026-05-14T10:30:05Z"
}
```

---

## Common Workflows

### 1. Generate and Approve Response
```python
# Generate
response = generator.generate(email, tone="friendly")

# Validate
safety = filter.validate(response.generated_text)

# If safe, record approval
if safety.is_safe:
    feedback = tracker.record_feedback(
        response_id=response.message_id,
        feedback_type="approved",
    )
    # reward = +10.0
```

### 2. Personalized Recommendation
```python
# Get best tone for this sender
tone = personalization.recommend_tone_for_sender(sender)

# Get hints
hints = personalization.get_personalization_hints()

# Generate with personalization
response = generator.generate(
    email,
    tone=tone,
    personalization=hints,
)
```

### 3. Tone Switching
```python
# Generate with one tone
response1 = generator.generate(email, tone="professional")

# User wants to try another
response2 = generator.regenerate_with_tone(response1, "friendly")
```

### 4. Collect Metrics
```python
# Get tone performance
perf = tracker.get_tone_performance()
# Output: approval_rate, avg_reward per tone

# Get per-sender stats
sender_stats = tracker.get_sender_performance("recruiter@company.com")

# Export for RL training
training_data = tracker.export_rl_training_data()
```

---

## Error Handling

### Response Generation Fails
```python
try:
    response = generator.generate(email)
except Exception as e:
    # Falls back to template
    response = generator._fallback_response(email, tone)
```

### Safety Issues
```python
result = filter.validate(text)

if result.severity == SafetySeverity.CRITICAL:
    # Requires approval
    requires_human_review = True
    
if result.warnings:
    # Display to user
    print(result.suggestions)
```

---

## Configuration

### Environment Variables
```bash
export GEMINI_API_KEY="your-api-key"
export GEMINI_MODEL="gemini-1.5-flash"  # or your model
```

### Safety Filter Modes
```python
# Default (lenient)
filter = SafetyFilter(strict_mode=False)

# Strict (requires review for warnings)
filter = SafetyFilter(strict_mode=True)
```

### Personalization Storage
```python
# Default location
memory = PersonalizationMemory()

# Custom location
memory = PersonalizationMemory(
    storage_path="/path/to/custom/storage.jsonl"
)
```

---

## Monitoring

### Check Response Stats
```
GET http://localhost:5000/api/responses/stats
```

Response:
```json
{
  "feedback_stats": {
    "total_feedbacks": 45,
    "approvals": 38,
    "approval_rate": 0.844
  },
  "tone_performance": {
    "professional": {"approval_rate": 0.87},
    "friendly": {"approval_rate": 0.92}
  }
}
```

### Check Health
```
GET http://localhost:8000/api/v1/responses/health
```

---

## Testing

```bash
# Test generation
python -c "
from app.workflow.response_generator import ResponseGenerator
from app.workflow.schemas import EmailRecord

gen = ResponseGenerator()
email = EmailRecord(
    id='test', thread_id='t1', sender='test@test.com',
    subject='test', body='test'
)
response = gen.generate(email)
print(response.generated_text)
"

# Test safety
python -c "
from app.workflow.safety_filter import SafetyFilter

filter = SafetyFilter()
result = filter.validate('I guarantee delivery Friday')
print(result.is_safe)  # False
print(result.violations)
"
```

---

## Integration Points

| Component | Integrates With | Purpose |
|-----------|-----------------|---------|
| Response Generator | Gemini API | AI generation |
| Safety Filter | Response Generator | Validation |
| Personalization | User Feedback | Learning |
| Feedback Tracker | DQN Agent | RL Rewards |
| Gmail Actions | FastAPI/Flask | Draft management |
| FastAPI Routes | UI components | REST API |
| Flask Routes | HTML forms | Web interface |

---

## Performance Tips

1. **Cache personalization**: Load once per session
2. **Batch operations**: Use email lists for bulk processing
3. **Monitor tokens**: Watch Gemini API usage
4. **Store efficiently**: JSONL is append-only, minimal overhead
5. **Async processing**: Use FastAPI async for I/O operations

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "API unavailable" | Set GEMINI_API_KEY, check internet |
| Low approval rates | Review tone_performance, adjust prompts |
| Safety too strict | Set strict_mode=False |
| Memory not persisting | Check data/ directory permissions |
| Slow generation | Add timeout handling, use fallbacks |
| Wrong tone recommended | Review personalization data, reset if needed |

---

## Next Development

- [ ] Add tests
- [ ] Implement caching
- [ ] Add batch processing
- [ ] Build analytics dashboard
- [ ] Multi-language support
- [ ] Template system
- [ ] A/B testing framework

---

**For detailed documentation, see:**
- `AI_RESPONSE_ASSISTANT.md` - Complete guide
- `IMPLEMENTATION_SUMMARY.md` - Full implementation details
- Component docstrings - In-code documentation
