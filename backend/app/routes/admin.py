from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from ..database import get_db
from ..auth import validate_admin_key
from ..models import Ticket, ApiKey, WebhookLog, AuditLog
from ..schemas import WebhookLogResponse, ApiKeyResponse
from ..services.ticket_service import TicketService

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.get("/tickets", dependencies=[Depends(validate_admin_key)])
async def get_all_tickets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all tickets (admin only)"""
    tickets = db.query(Ticket).offset(skip).limit(limit).all()
    return [
        {
            "id": t.id,
            "ticket_text": t.ticket_text[:100] + "..." if len(t.ticket_text) > 100 else t.ticket_text,
            "label": t.label,
            "confidence": t.confidence,
            "api_key": t.api_key,
            "created_at": t.created_at.isoformat(),
            "processing_time": t.processing_time
        }
        for t in tickets
    ]


@router.get("/api-keys", dependencies=[Depends(validate_admin_key)])
async def get_all_api_keys(db: Session = Depends(get_db)):
    """Get all API keys (admin only)"""
    api_keys = db.query(ApiKey).all()
    return [
        ApiKeyResponse(
            key=k.key,
            customer_id=k.customer_id,
            rate_limit=k.rate_limit,
            requests_today=k.requests_today,
            is_active=k.is_active
        )
        for k in api_keys
    ]


@router.get("/webhook-logs", dependencies=[Depends(validate_admin_key)])
async def get_webhook_logs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get webhook processing logs (admin only)"""
    logs = db.query(WebhookLog).order_by(WebhookLog.created_at.desc()).offset(skip).limit(limit).all()
    return [
        WebhookLogResponse(
            id=log.id,
            provider=log.provider,
            status_code=log.status_code,
            processing_time=log.processing_time,
            created_at=log.created_at
        )
        for log in logs
    ]


@router.delete("/old-tickets", dependencies=[Depends(validate_admin_key)])
async def delete_old_tickets(
    days: int = 90,
    db: Session = Depends(get_db)
):
    """Delete tickets older than specified days (GDPR compliance)"""
    ticket_service = TicketService(db)
    deleted_count = ticket_service.delete_old_tickets(days)
    logger.info(f"Admin deleted {deleted_count} old tickets")
    return {"message": f"Deleted {deleted_count} tickets older than {days} days"}


@router.get("/stats", dependencies=[Depends(validate_admin_key)])
async def get_admin_stats(db: Session = Depends(get_db)):
    """Get comprehensive admin statistics"""
    # Ticket stats
    total_tickets = db.query(Ticket).count()
    tickets_today = db.query(Ticket).filter(
        Ticket.created_at >= db.query(db.func.date(Ticket.created_at)).distinct().order_by(db.func.date(Ticket.created_at).desc()).first()[0]
    ).count()

    # API key stats
    total_api_keys = db.query(ApiKey).count()
    active_api_keys = db.query(ApiKey).filter(ApiKey.is_active == True).count()

    # Processing stats
    avg_processing_time = db.query(db.func.avg(Ticket.processing_time)).filter(Ticket.processing_time.isnot(None)).scalar()
    avg_processing_time = float(avg_processing_time) if avg_processing_time else 0.0

    # Label distribution
    label_counts = db.query(Ticket.label, db.func.count(Ticket.id)).group_by(Ticket.label).all()
    label_distribution = {label: count for label, count in label_counts}

    return {
        "tickets": {
            "total": total_tickets,
            "today": tickets_today
        },
        "api_keys": {
            "total": total_api_keys,
            "active": active_api_keys
        },
        "performance": {
            "avg_processing_time": round(avg_processing_time, 3)
        },
        "distribution": label_distribution
    }


@router.post("/maintenance/cleanup", dependencies=[Depends(validate_admin_key)])
async def run_maintenance_cleanup(db: Session = Depends(get_db)):
    """Run maintenance cleanup tasks"""
    # Clean old audit logs (keep last 1000)
    old_audit_logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(1000).all()
    for log in old_audit_logs:
        db.delete(log)

    # Clean old webhook logs (keep last 500)
    old_webhook_logs = db.query(WebhookLog).order_by(WebhookLog.created_at.desc()).offset(500).all()
    for log in old_webhook_logs:
        db.delete(log)

    db.commit()

    deleted_audit = len(old_audit_logs)
    deleted_webhook = len(old_webhook_logs)

    logger.info(f"Maintenance cleanup: deleted {deleted_audit} audit logs, {deleted_webhook} webhook logs")

    return {
        "message": "Maintenance cleanup completed",
        "deleted_audit_logs": deleted_audit,
        "deleted_webhook_logs": deleted_webhook
    }