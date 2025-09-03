from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class TicketRequest(BaseModel):
    ticket_text: str = Field(..., min_length=10, max_length=10000, description="The customer support ticket text to classify")

    class Config:
        schema_extra = {
            "example": {
                "ticket_text": "I was charged twice this month for my premium subscription. Please refund the duplicate payment."
            }
        }


class TicketResponse(BaseModel):
    label: str = Field(..., description="Classification label: bug, feature_request, billing_issue, or other")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    summary: str = Field(..., description="AI-generated summary of the ticket")

    class Config:
        schema_extra = {
            "example": {
                "label": "billing_issue",
                "confidence": 0.95,
                "summary": "Customer reporting duplicate charges and requesting refund."
            }
        }


class TicketStats(BaseModel):
    total_tickets: int = Field(..., description="Total number of tickets processed")
    avg_confidence: float = Field(..., description="Average confidence score")
    label_distribution: Dict[str, int] = Field(..., description="Distribution of ticket labels")
    avg_processing_time: float = Field(..., description="Average processing time in seconds")


class ApiKeyCreate(BaseModel):
    customer_id: str = Field(..., description="Stripe customer ID")
    rate_limit: Optional[int] = Field(100, description="Daily request limit")


class ApiKeyResponse(BaseModel):
    key: str = Field(..., description="API key")
    customer_id: str = Field(..., description="Associated Stripe customer ID")
    rate_limit: int = Field(..., description="Daily request limit")
    requests_today: int = Field(..., description="Requests used today")
    is_active: bool = Field(..., description="Whether the key is active")


class WebhookLogResponse(BaseModel):
    id: int
    provider: str
    status_code: int
    processing_time: float
    created_at: datetime


class HealthCheck(BaseModel):
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="API version")
    uptime: str = Field(..., description="Service uptime")
    database: str = Field(..., description="Database connection status")


class MetricsResponse(BaseModel):
    total_tickets: int
    total_api_keys: int
    avg_processing_time: float
    uptime_seconds: int
    memory_usage: Dict[str, float]


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict] = Field(None, description="Additional error details")