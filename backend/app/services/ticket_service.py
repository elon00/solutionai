import logging
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models import Ticket, ApiKey, User
from ..config import settings
from .ai_service import ai_service


logger = logging.getLogger(__name__)


class TicketService:
    def __init__(self, db: Session):
        self.db = db

    async def process_ticket(self, ticket_text: str, api_key: str, user_id: Optional[int] = None) -> Ticket:
        """Process a ticket through AI classification and save to database"""

        # Check rate limit
        await self._check_rate_limit(api_key)

        # Classify with AI
        classification = await ai_service.classify_ticket(ticket_text)

        # Create ticket record
        ticket = Ticket(
            ticket_text=ticket_text,
            label=classification['label'],
            confidence=classification['confidence'],
            summary=classification['summary'],
            api_key=api_key,
            user_id=user_id,
            source="api",
            status="processed",
            processing_time=classification.get('processing_time', 0)
        )

        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)

        logger.info(f"Ticket processed: {ticket.id} - {ticket.label} ({ticket.confidence:.2f})")
        return ticket

    async def _check_rate_limit(self, api_key: str):
        """Check and update rate limit for API key"""
        today = date.today()

        api_key_obj = self.db.query(ApiKey).filter(ApiKey.key == api_key).first()
        if not api_key_obj:
            raise ValueError("Invalid API key")

        # Reset counter if it's a new day
        if api_key_obj.last_reset != today:
            api_key_obj.requests_today = 0
            api_key_obj.last_reset = today

        # Check limit
        if api_key_obj.requests_today >= api_key_obj.rate_limit:
            raise ValueError("Rate limit exceeded")

        # Increment counter
        api_key_obj.requests_today += 1
        self.db.commit()

    def get_recent_tickets(self, api_key: str, limit: int = 10) -> List[Ticket]:
        """Get recent tickets for an API key"""
        return self.db.query(Ticket).filter(
            Ticket.api_key == api_key
        ).order_by(Ticket.created_at.desc()).limit(limit).all()

    def get_ticket_stats(self, api_key: str) -> dict:
        """Get statistics for tickets processed with this API key"""
        tickets = self.db.query(Ticket).filter(Ticket.api_key == api_key).all()

        if not tickets:
            return {
                "total_tickets": 0,
                "avg_confidence": 0,
                "label_distribution": {},
                "avg_processing_time": 0
            }

        total_tickets = len(tickets)
        avg_confidence = sum(t.confidence for t in tickets) / total_tickets
        avg_processing_time = sum(t.processing_time or 0 for t in tickets) / total_tickets

        label_distribution = {}
        for ticket in tickets:
            label_distribution[ticket.label] = label_distribution.get(ticket.label, 0) + 1

        return {
            "total_tickets": total_tickets,
            "avg_confidence": round(avg_confidence, 3),
            "label_distribution": label_distribution,
            "avg_processing_time": round(avg_processing_time, 3)
        }

    def get_all_tickets(self, skip: int = 0, limit: int = 100) -> List[Ticket]:
        """Get all tickets (admin function)"""
        return self.db.query(Ticket).offset(skip).limit(limit).all()

    def delete_old_tickets(self, days: int = 90):
        """Delete tickets older than specified days (GDPR compliance)"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = self.db.query(Ticket).filter(
            Ticket.created_at < cutoff_date
        ).delete()
        self.db.commit()
        logger.info(f"Deleted {deleted_count} old tickets")
        return deleted_count