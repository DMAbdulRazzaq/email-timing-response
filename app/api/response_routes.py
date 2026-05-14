"""
Response Generation API Routes — FastAPI endpoints for AI response drafting.

Provides endpoints for:
- Generating AI response drafts
- Managing drafts (update, preview, send)
- Tracking feedback
- Personalization
"""

import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.workflow.personalization_memory import PersonalizationMemory
from app.workflow.response_feedback import ResponseFeedbackTracker
from app.workflow.response_generator import ResponseGenerator
from app.workflow.safety_filter import SafetyFilter
from app.workflow.schemas import EmailRecord, ThreadContext
from app.workflow.thread_context import fetch_thread_context
from monitoring.logging_config import get_logger

logger = get_logger(__name__)

# Initialize components
response_generator = ResponseGenerator()
safety_filter = SafetyFilter(strict_mode=False)
personalization_memory = PersonalizationMemory()
feedback_tracker = ResponseFeedbackTracker()

router = APIRouter(prefix="/api/v1/responses", tags=["response-generation"])


# ── Request/Response Models ──────────────────────────────────────────────────

class GenerateResponseRequest(BaseModel):
    """Request to generate AI response."""
    message_id: str
    thread_id: str
    sender: str
    subject: str
    body: str
    tone: str = "professional"
    max_length: int = 500
    require_approval: bool = True


class GeneratedResponseDTO(BaseModel):
    """Response DTO for generated response."""
    response_id: str
    message_id: str
    generated_text: str
    tone_used: str
    confidence: float
    warnings: list[str]
    requires_approval: bool
    safety_check: dict[str, Any]


class RegenerateRequest(BaseModel):
    """Request to regenerate with different tone."""
    response_id: str
    new_tone: str


class FeedbackRequest(BaseModel):
    """Record feedback on generated response."""
    response_id: str
    feedback_type: str  # approved|edited|rejected
    edited_text: str = ""
    approval_time_seconds: float = 0.0
    feedback_notes: str = ""


class DraftPreviewDTO(BaseModel):
    """Preview of a saved draft."""
    draft_id: str
    to: str
    subject: str
    snippet: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=GeneratedResponseDTO)
async def generate_response(request: GenerateResponseRequest):
    """
    Generate an AI response draft for an email.
    
    Process:
    1. Build email context
    2. Fetch thread history
    3. Generate response with Gemini
    4. Run safety checks
    5. Return for approval
    """
    try:
        logger.info(f"Generating response for {request.message_id} with tone={request.tone}")
        
        # Create email record
        email = EmailRecord(
            id=request.message_id,
            thread_id=request.thread_id,
            sender=request.sender,
            subject=request.subject,
            body=request.body,
        )
        
        # Get personalization hints
        personalization = personalization_memory.get_personalization_hints()
        recommended_tone = personalization_memory.recommend_tone_for_sender(request.sender)
        
        # Generate response
        start_time = time.time()
        generated = response_generator.generate(
            email=email,
            tone=request.tone,
            personalization=personalization,
            max_length=request.max_length,
        )
        generation_time = time.time() - start_time
        
        # Run safety checks
        safety_result = safety_filter.validate(
            generated.generated_text,
            sender=request.sender,
            context={"category": "auto_reply"}
        )
        
        requires_approval = (
            request.require_approval or
            not safety_result.is_safe or
            generated.confidence < 0.7
        )
        
        logger.info(
            f"Generated response: {generated.response_id}, "
            f"safe={safety_result.is_safe}, "
            f"time={generation_time:.2f}s"
        )
        
        return GeneratedResponseDTO(
            response_id=generated.message_id,
            message_id=request.message_id,
            generated_text=generated.generated_text,
            tone_used=generated.tone_used,
            confidence=generated.confidence,
            warnings=generated.warnings + safety_result.warnings,
            requires_approval=requires_approval,
            safety_check=safety_result.to_dict(),
        )
    
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regenerate", response_model=GeneratedResponseDTO)
async def regenerate_with_tone(request: RegenerateRequest):
    """
    Regenerate response with different tone.
    
    Useful for tone selection UI where user wants to try another tone.
    """
    try:
        if request.new_tone not in response_generator.SUPPORTED_TONES:
            raise ValueError(f"Unsupported tone: {request.new_tone}")
        
        logger.info(f"Regenerating {request.response_id} with tone={request.new_tone}")
        
        personalization = personalization_memory.get_personalization_hints()
        
        # This is a simplified regeneration - in production would fetch original email
        # from database or cache
        email = EmailRecord(
            id=request.response_id,
            thread_id="",
            sender="",
            subject="",
            body="",
        )
        
        generated = response_generator.generate(
            email=email,
            tone=request.new_tone,
            personalization=personalization,
        )
        
        safety_result = safety_filter.validate(generated.generated_text)
        
        return GeneratedResponseDTO(
            response_id=generated.message_id,
            message_id=request.response_id,
            generated_text=generated.generated_text,
            tone_used=generated.tone_used,
            confidence=generated.confidence,
            warnings=generated.warnings + safety_result.warnings,
            requires_approval=not safety_result.is_safe,
            safety_check=safety_result.to_dict(),
        )
    
    except Exception as e:
        logger.error(f"Error regenerating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def record_feedback(request: FeedbackRequest):
    """
    Record user feedback on AI-generated response.
    
    This feedback:
    - Updates personalization memory
    - Generates RL reward signals
    - Improves future generations
    """
    try:
        logger.info(f"Recording feedback: {request.feedback_type} for {request.response_id}")
        
        feedback = feedback_tracker.record_feedback(
            response_id=request.response_id,
            sender="unknown",  # Would come from context
            original_action="reply_now",
            generated_tone="professional",
            feedback_type=request.feedback_type,
            approval_time_seconds=request.approval_time_seconds,
            feedback_notes=request.feedback_notes,
        )
        
        # Also record in personalization memory
        personalization_memory.record_action(
            response_id=request.response_id,
            sender="unknown",
            action=request.feedback_type,
            tone="professional",
            generated_text="",
            user_text=request.edited_text if request.feedback_type == "edited" else "",
            feedback=request.feedback_notes,
        )
        
        return {
            "status": "recorded",
            "reward": feedback.reward_signal,
            "feedback_type": request.feedback_type,
        }
    
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/stats")
async def get_feedback_stats():
    """Get feedback statistics for analysis."""
    try:
        return {
            "session_stats": feedback_tracker.get_session_stats(),
            "tone_performance": feedback_tracker.get_tone_performance(),
            "filter_stats": safety_filter.get_stats(),
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personalization/profile")
async def get_personalization_profile():
    """Get user's personalization profile."""
    try:
        return personalization_memory.export_profile()
    except Exception as e:
        logger.error(f"Error fetching profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tones/supported")
async def get_supported_tones():
    """Get list of supported tones."""
    return {
        "tones": response_generator.SUPPORTED_TONES,
        "descriptions": {
            tone: response_generator._get_tone_description(tone)
            for tone in response_generator.SUPPORTED_TONES
        },
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "components": {
            "response_generator": "ready",
            "safety_filter": "ready",
            "personalization": "ready",
            "feedback_tracker": "ready",
        },
    }
