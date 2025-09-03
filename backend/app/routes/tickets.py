from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..services.ticket_service import TicketService
from ..models import Ticket
from ..schemas import TicketRequest, TicketResponse, TicketStats
from ..auth import get_current_api_key
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["tickets"])


@router.post("/triage", response_model=TicketResponse)
async def triage_ticket(
    request: Request,
    ticket: TicketRequest,
    api_key: str = Depends(get_current_api_key),
    db: Session = Depends(get_db)
):
    """
    Classify and triage a customer support ticket using AI.

    - **ticket_text**: The text content of the customer ticket
    - **api_key**: Your API key (passed in X-Api-Key header)
    """
    try:
        ticket_service = TicketService(db)
        processed_ticket = await ticket_service.process_ticket(
            ticket_text=ticket.ticket_text,
            api_key=api_key
        )

        return TicketResponse(
            label=processed_ticket.label,
            confidence=processed_ticket.confidence,
            summary=processed_ticket.summary
        )

    except ValueError as e:
        if "Rate limit exceeded" in str(e):
            raise HTTPException(status_code=429, detail=str(e))
        elif "Invalid API key" in str(e):
            raise HTTPException(status_code=401, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing ticket: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/recent", response_model=List[dict])
async def get_recent_tickets(
    request: Request,
    api_key: str = Depends(get_current_api_key),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """
    Get recent tickets processed with your API key.

    - **limit**: Maximum number of tickets to return (default: 10)
    """
    try:
        ticket_service = TicketService(db)
        tickets = ticket_service.get_recent_tickets(api_key, limit)

        return [
            {
                "ticket_text": t.ticket_text,
                "label": t.label,
                "confidence": t.confidence,
                "summary": t.summary,
                "timestamp": t.created_at.isoformat(),
                "processing_time": t.processing_time
            }
            for t in tickets
        ]

    except Exception as e:
        logger.error(f"Error fetching recent tickets: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats", response_model=TicketStats)
async def get_ticket_stats(
    request: Request,
    api_key: str = Depends(get_current_api_key),
    db: Session = Depends(get_db)
):
    """
    Get statistics for tickets processed with your API key.
    """
    try:
        ticket_service = TicketService(db)
        stats = ticket_service.get_ticket_stats(api_key)
        return TicketStats(**stats)

    except Exception as e:
        logger.error(f"Error fetching ticket stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")