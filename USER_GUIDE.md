# AI Response Assistant — User Guide

## How to Use the AI Response Assistant

This guide walks through a real-world scenario of using the AI Response Assistant to draft professional email responses.

---

## Scenario: Email from a Recruiter

**Incoming Email**:
```
From: sarah@techcorp.com
Subject: Exciting Software Engineer Role - 200k+ salary
Body:
Hi there! We've been impressed by your profile. We have an exciting opportunity 
for a Senior Software Engineer at our San Francisco office. The role involves 
building distributed systems at scale. Interested in chatting more? We're flexible 
on timing and compensation.

Looking forward to hearing from you!
Best,
Sarah
```

---

## Step 1: Email Prioritization (DQN Agent)

The email is analyzed by your existing DQN agent:

```
Email Features:
- Priority: 85/100 (from recruiter, clear opportunity)
- Sender Importance: 3/5 (new company, recruiter)
- Waiting Time: 2 minutes
- Workload: Medium
- Time of Day: 10:00 AM

DQN Recommendation: REPLY_NOW (confidence: 0.92)
```

---

## Step 2: Click "Generate AI Reply"

In the dashboard, you see the email card with an "AI Reply" button.

```
┌─────────────────────────────────────────────────┐
│  From: sarah@techcorp.com                       │
│  Subject: Exciting Software Engineer Role       │
│  Priority: ████████░ 85/100                     │
│                                                  │
│  [Generate AI Reply] ← Click here                │
│  [Archive] [Mark Important]                     │
└─────────────────────────────────────────────────┘
```

---

## Step 3: AI Panel Opens

A beautiful panel appears with AI-generated response:

```
┌─────────────────────────────────────────────────────────────────┐
│                   🤖 AI Response Assistant                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Tone: [Professional ▼]   [Friendly] [Concise] [Enthusiastic]   │
│                                                                   │
│ ──────────────────────────────────────────────────────────────── │
│ Generated Response:                      Confidence: 91%          │
│                                         342 characters            │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Dear Sarah,                                                │ │
│ │                                                            │ │
│ │ Thank you for reaching out about this opportunity at      │ │
│ │ TechCorp. I'm genuinely interested in learning more about │ │
│ │ the distributed systems engineering role. Your mention of │ │
│ │ flexibility on timing is appreciated. I'd be happy to     │ │
│ │ discuss further at your convenience.                      │ │
│ │                                                            │ │
│ │ Best regards,                                             │ │
│ │ [Your Name]                                               │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│ ✓ Approve & Draft    ✏️ Edit & Save    🔄 Regenerate    ✗ Reject│
│                                                                   │
│ 📋 Generation Context:                                           │
│    Thread Summary: First email from recruiter                   │
│    Detected Tone: Friendly and professional                     │
│    Urgency: Medium (consider within 48 hours)                   │
│    Recommendation: Concise professional acknowledgment          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step 4a: Change Tone (Optional)

Want a friendlier tone? Click "Friendly" and the response regenerates:

```
Tone: [Professional] [Friendly ✓] [Concise] [Enthusiastic]

Generated Response (Friendly Tone):
─────────────────────────────────────────────────
Hey Sarah!

Thanks so much for thinking of me – this opportunity at TechCorp 
sounds awesome! I'm definitely interested in learning more about 
the distributed systems work you mentioned. I love the flexibility 
you're offering, that's really appreciated. 

Let's chat soon!

Cheers,
[Your Name]
─────────────────────────────────────────────────

[Much shorter, warm tone - 201 chars]
```

---

## Step 4b: Edit Manually (Optional)

Don't like something? Edit directly in the textarea:

```
┌─────────────────────────────────────────┐
│ Generated Response:                      │
│ ┌───────────────────────────────────────┐ │
│ │ Dear Sarah,                           │ │
│ │                                       │ │
│ │ Thank you for reaching out about the  │ │
│ │ Software Engineer role at TechCorp.   │ │
│ │ This sounds like a great fit for my   │ │
│ │ experience with distributed systems.  │ │
│ │                                       │ │
│ │ I'd love to discuss further. I'm      │ │
│ │ available next week.  ← EDITED THIS   │ │
│ │                                       │ │
│ │ Best regards,                         │ │
│ │ [Your Name]                           │ │
│ └───────────────────────────────────────┘ │
│ 389 characters (auto-updated counter)     │
└─────────────────────────────────────────┘
```

---

## Step 5: Check for Safety Issues

The system validates for safety:

```
✓ No safety violations detected
No warnings found
Ready to send

Confidence: 91%
Tone: Professional
```

BUT if there was an issue:

```
⚠️ Safety Check:
- Detected commitment pattern: "will discuss"
- Consider: "I'd be happy to discuss"

Suggestions:
1. Replace absolute commitments with "happy to"
2. Add "if interested" qualifiers
3. Review scheduling statements

→ Manual review recommended
```

---

## Step 6: Approve & Create Draft

Click "✓ Approve & Draft":

```
Send Email Response?
This will send the response to: sarah@techcorp.com

┌──────────────────────────────────────┐
│ [Send Now]  [Save as Draft]  [Cancel] │
└──────────────────────────────────────┘
```

---

## Step 7: Draft Created in Gmail

Gmail draft is created with:
- Recipient: sarah@techcorp.com
- Subject: Re: Exciting Software Engineer Role...
- Body: Your approved response
- Label: AI/Draft
- Header: X-AI-Generated: true

```
Gmail Draft:
┌────────────────────────────────────────────┐
│ Draft saved for: sarah@techcorp.com        │
│ Subject: Re: Exciting Software Engineer... │
│ Preview: "Dear Sarah, Thank you for..."    │
│                                             │
│ [Edit in Gmail]  [Send]  [View]           │
└────────────────────────────────────────────┘
```

---

## Step 8: System Learns from Your Action

**Behind the Scenes**:

1. **Record Feedback**
   ```python
   feedback = tracker.record_feedback(
       response_id="resp_sarah_123",
       sender="sarah@techcorp.com",
       feedback_type="approved",  # User approved
       approval_time_seconds=12.3,  # Took 12 seconds
   )
   # Reward: +10.0
   ```

2. **Update Personalization**
   ```python
   memory.record_action(
       sender="sarah@techcorp.com",
       action="approved",
       tone="professional",
       # Learned: This sender responds well to professional tone
   )
   ```

3. **Generate RL Signal**
   ```python
   # Next time you get an email from "recruiter@company.com":
   recommended_tone = "professional"  # Learned from this interaction
   ```

---

## Step 9: Viewing Statistics

After several interactions, check the dashboard:

```
📊 AI Response Statistics

Tone Performance:
┌─────────────┬────────────┬──────────┐
│ Tone        │ Approval % │ Avg Reward│
├─────────────┼────────────┼──────────┤
│ Friendly    │ 92%        │ 10.1     │
│ Professional│ 87%        │ 9.2      │
│ Formal      │ 78%        │ 8.5      │
│ Concise     │ 85%        │ 9.0      │
└─────────────┴────────────┴──────────┘

Sender-Specific Insights:
- sarah@techcorp.com: Prefers professional tone
  (3/3 interactions approved with professional)
  
- john@company.com: Prefers friendly tone
  (4/5 interactions approved with friendly)

Overall Metrics:
- Total Responses Generated: 23
- Approval Rate: 87% (20/23)
- Average Response Time: 8.2 seconds
- Safety Filter Violations: 2 (strict mode would've flagged)
```

---

## Different Scenarios

### Scenario 2: Email from Your Boss

```
From: boss@company.com
Subject: Project Update

Email Analysis:
- Priority: 95/100
- Sender Importance: 5/5
- Urgency: Immediate

AI Panel:
Tone suggestion: Professional (learned from history)

"Hi [Boss], Thanks for reaching out. I'll have the 
project update to you by end of day. Looking forward 
to discussing next steps."

Status: Safe ✓
Confidence: 94%
[✓ Approve & Draft] ✏️ [Edit] 🔄 [Regenerate] ✗ [Reject]
```

### Scenario 3: Email from Unknown Sender

```
From: unknown@random.com
Subject: Business Opportunity

Email Analysis:
- Priority: 25/100 (likely spam)
- Sender Importance: 1/5

AI Panel:
(Opens anyway for review)

"Dear Unknown Person, Thank you for reaching out.
I'm not interested at this time."

Status: ⚠️ Safety warning
- May sound curt/rude to legitimate contacts
- Suggestion: Add "but appreciate you thinking of me"

[✓ Approve & Draft] ✏️ [Edit] 🔄 [Regenerate] ✗ [Reject]
```

---

## Rejection Example

```
From: newsletter@company.com
Subject: Weekly Newsletter

Generated Draft:
"Hi Newsletter, Thanks for sending. I'll read this soon."

User Rejects: [✗ Reject button]

System Records:
- Response ID: resp_newsletter_456
- Feedback Type: "rejected"
- Reward: -5.0
- Learning: "This sender doesn't need replies"

Next time from this sender:
- System remembers: Don't generate replies for newsletters
- Recommendation: "archive"
```

---

## Edit Example

```
Original Generated:
"Thank you for the opportunity. I'm very interested."

User Edits to:
"Thanks! This sounds like an amazing opportunity. 
I'm definitely interested in learning more."

User Clicks: [✏️ Edit & Save]

System Records:
- Original confidence: 85%
- User edited: +2 reward (learning signal)
- Edit distance: 67 chars changed
- Learning: "This sender prefers more enthusiasm and detail"
```

---

## Real Numbers After 1 Week

```
Email Volume: 145 emails
AI Responses Generated: 34
Approval Rate: 89% (30 approved, 3 edited, 1 rejected)

Top Performers (Tone Effectiveness):
1. Friendly: 92% approval (12/13 emails)
2. Professional: 88% approval (14/16 emails)
3. Concise: 85% approval (11/13 emails)

Sender Learnings:
- recruiter@techcorp.com → Professional (100% approval)
- colleague@company.com → Friendly (92% approval)
- boss@company.com → Professional (100% approval)

Safety Filter:
- 34 responses generated
- 2 flagged for review (5.9%)
- 0 actually unsafe (strict review)

RL Feedback Integration:
- 30 approval signals (+10 each) = +300 reward
- 3 edit signals (+2 each) = +6 reward
- 1 rejection signal (-5) = -5 reward
- Total session reward: +301
→ Strong positive signal for DQN training
```

---

## Mobile View

The AI panel is responsive:

```
Mobile (320px width):
┌──────────────────┐
│ 🤖 AI Response   │
├──────────────────┤
│                  │
│ Tone: [Prof ▼]   │
│                  │
│ Generated:       │
│ ┌──────────────┐ │
│ │ Thank you    │ │
│ │ for your     │ │
│ │ email...     │ │
│ └──────────────┘ │
│ 89% conf 234 ch  │
│                  │
│ [✓ Approve]      │
│ [✏️ Edit]        │
│ [🔄 Regen]       │
│ [✗ Reject]       │
│                  │
│ 📋 Context       │
│ ► Show details   │
│                  │
└──────────────────┘
```

---

## Keyboard Shortcuts (Future)

```
Ctrl+1  → Approve & Draft
Ctrl+2  → Edit & Save
Ctrl+3  → Regenerate
Ctrl+4  → Reject
Tab     → Switch tones
Enter   → Quick approve
```

---

## Tips & Best Practices

### 1. First-time Setup
- Set GEMINI_API_KEY environment variable
- Ensure Gmail API is configured
- Test with 3-5 emails to warm up personalization

### 2. Consistent Results
- Use same tone for similar senders (builds history)
- Provide feedback promptly (system learns faster)
- Review auto-generated responses before sending

### 3. Personalization
- The system learns after ~5 interactions per sender
- Edits are valuable learning signals
- Rejections help avoid bad patterns

### 4. Safety
- Strict mode: For compliance-heavy industries
- Review mode: For first-time senders
- Custom patterns: Add if you have domain-specific needs

### 5. Performance
- System gets faster as it learns (fewer regenerations needed)
- Batch processing for newsletters/bulk
- Archive low-priority senders to focus on important contacts

---

## Workflow Integration

### Complete Email Response Flow

```
1. Email Arrives
   ↓
2. DQN Prioritizes → "reply_now"
   ↓
3. User Clicks "Generate AI Reply"
   ↓
4. Gemini Generates → "Dear Sarah..."
   ↓
5. Safety Filter Checks → ✓ Safe
   ↓
6. UI Shows Draft with Tone Options
   ↓
7. User Reviews & Approves (or edits)
   ↓
8. Gmail Draft Created
   ↓
9. Feedback Recorded → +10 reward
   ↓
10. Personalization Updated → Learn tone preference
   ↓
11. RL Signal Feeds Back → Improve future prioritization
```

---

## Success Metrics

Track these to measure success:

- **Approval Rate**: >80% means good generation
- **Edit Rate**: <10% means highly accurate
- **Rejection Rate**: <5% means few misses
- **Response Time**: <30sec to approve/edit
- **Safety Issues**: <5% false positives
- **Sender Personalization**: 3+ tones per sender

---

## Troubleshooting

**Q: Why did the AI suggest the wrong tone?**
A: The system learns from your feedback. Keep approving/rejecting to refine recommendations.

**Q: Can I turn off AI responses?**
A: Yes, just don't click "Generate AI Reply". System learns what you ignore.

**Q: Will my edits be learned?**
A: Yes! Every edit is recorded and improves future generation for that sender.

**Q: What if the API fails?**
A: System uses template fallback - you'll still get a reasonable response.

**Q: How do I reset personalization?**
A: Delete `data/draft_interactions.jsonl` to start fresh learning.

---

## Next Steps

1. Set up API keys
2. Run services
3. Try generating first AI response
4. Approve/edit several responses
5. Check statistics dashboard
6. Observe personalization in action
7. Adjust safety settings if needed
8. Monitor RL reward signals

**You're now an AI email communication master! 🚀**
