# Next Stage Architecture: Intelligent Gmail Workflow Automation

## Product Goal

Transform the project from an email classifier into a human-approved workflow automation
platform that learns a user's inbox preferences over time.

## Target Pipeline

```text
Gmail Inbox
-> OAuth Authentication
-> Email Fetcher
-> Email Parser
-> Cleaning + Preprocessing
-> Feature Engineering
-> RL Prioritization Engine
-> Gemini Context Engine
-> Action Recommendation Engine
-> Human Approval Layer
-> Gmail Auto Actions
-> Analytics Dashboard
-> Feedback + Retraining
```

## New Module Layout

```text
app/workflow/
  schemas.py            Typed records for emails, threads, feedback, recommendations
  preprocessing.py      Gmail MIME parsing, body decoding, text cleaning
  priority_engine.py    Rule-based score and category baseline
  thread_context.py     Thread history and follow-up extraction
  gemini_engine.py      Gemini summarization, tone, action, reply drafting
  recommender.py        Combines priority, thread context, Gemini, safety rules
  feedback.py           Converts human corrections into rewards
  gmail_actions.py      Labels, archive, important, draft creation after approval
  analytics.py          Dashboard metrics from recommendations and rewards
  storage.py            Append-only JSONL event storage

scripts/
  run_intelligent_workflow.py
```

## Reinforcement Learning Feedback Loop

The production loop should optimize actions from human correction data, not only synthetic
reward tables.

State features:

- priority score normalized to `[0, 1]`
- sender importance
- thread follow-up count
- waiting time
- deadline/action keyword density
- Gemini confidence
- previous user behavior for sender/domain

Actions:

- `reply_now`
- `delay_reply`
- `mark_important`
- `archive`

Reward examples:

| Recommended | User Action | Reward |
|---|---:|---:|
| `reply_now` | `reply_now` | +10 |
| `mark_important` | `mark_important` | +7 |
| `archive` | `reply_now` | -10 |
| `reply_now` | `archive` | -8 |

Implementation strategy:

1. Store every recommendation in `data/recommendations.jsonl`.
2. Store every approval/correction in `data/feedback_events.jsonl`.
3. Convert corrections into replay-buffer transitions.
4. Run nightly or manual retraining with MLflow tracking.
5. Promote a model only if offline replay evaluation improves.

## Gemini Context Engine

Gemini should be used for bounded intelligence, not blind autonomy.

Use Gemini for:

- one-sentence email summary
- tone detection
- urgency reasoning
- reply draft generation
- action recommendation
- risk detection

Prompting rules:

- Require JSON output.
- Restrict actions to known enum values.
- Pass only necessary email text.
- Include thread summary instead of dumping entire private history when possible.
- Keep temperature low for reliable workflow decisions.
- Never let Gemini directly send mail.

## Thread-Aware Intelligence

Thread context improves prioritization when:

- a sender has followed up repeatedly
- the same deadline appears across messages
- the latest message is a reminder
- the user has already delayed the thread

Current implementation:

- `thread_context.fetch_thread_context(...)`
- counts follow-up terms
- summarizes recent thread senders/subjects
- raises scoring through `score_email(..., follow_up_count=...)`

## Human Approval Safety Layer

Automation levels:

| Action | Approval |
|---|---|
| Create recommendation | No approval needed |
| Add AI label | Approval recommended during beta |
| Archive promotion | Approval required until trust threshold is reached |
| Mark important | Approval required |
| Create reply draft | Approval required |
| Send email | Always manual approval |

The system should create drafts, not send replies.

## Gmail Automation

Implemented helpers:

- create labels like `AI/Reply Now`, `AI/Important`
- apply approved labels
- archive approved messages
- star delayed replies
- create reply drafts

Recommended next endpoint:

```text
POST /workflow/approve
{
  "message_id": "...",
  "thread_id": "...",
  "approved_action": "mark_important",
  "recommended_action": "reply_now",
  "notes": "Important but not urgent"
}
```

This endpoint should:

1. record feedback reward
2. apply Gmail action
3. create draft if needed
4. update analytics
5. log metrics to MLflow

## Analytics Dashboard

Dashboard metrics:

- total emails processed
- priority distribution
- action distribution
- sender importance ranking
- average reward
- reward trend
- correction rate
- approval rate
- top automation risks

## MLflow Strategy

Track training:

- algorithm
- state schema version
- reward schema version
- exploration rate
- replay buffer size
- reward mean and variance
- correction accuracy
- per-action precision
- model artifact

Track production inference:

- recommendation count
- confidence distribution
- approval rate
- override rate
- average reward from corrections
- latency

Model promotion rule:

Promote only when the candidate model improves correction-aligned reward and does not
increase unsafe action rate for `archive` or reply drafting.

## Scalability Plan

Local prototype:

- Gmail fetch script
- JSONL event store
- Streamlit/Flask dashboard
- MLflow local tracking

Production version:

- PostgreSQL for emails, recommendations, feedback
- Redis queue for background Gmail processing
- Celery/RQ worker for Gemini and Gmail API calls
- scheduler for periodic inbox sync
- object storage for model artifacts
- MLflow tracking server

## Security Practices

- Never commit OAuth client secrets or tokens.
- Keep `GEMINI_API_KEY` in environment variables.
- Store only sanitized email content when possible.
- Add explicit approval before destructive actions.
- Use least-privilege Gmail scopes for each mode.
- Encrypt tokens in production.
- Add audit logs for every Gmail mutation.

## Next Implementation Milestones

1. Add approval endpoint and UI buttons.
2. Move live Gmail fetch from `test_gmail.py` into reusable workflow services.
3. Persist recommendation and feedback events.
4. Add Streamlit analytics page backed by `app/workflow/analytics.py`.
5. Add retraining script that loads `feedback_events.jsonl`.
6. Log feedback reward and override rate to MLflow.
7. Add safe Gmail label/draft actions behind approval.
