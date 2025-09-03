from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import openai
import anthropic
from datetime import datetime
import json
from typing import Optional
import stripe
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI(title="Solution AI Ticket Triage SaaS", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Observability
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
FastAPIInstrumentor.instrument_app(app)

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ALLOWED_API_KEYS = os.getenv("ALLOWED_API_KEYS", "").split(",")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres:5432/solution_ai")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

openai.api_key = OPENAI_API_KEY
stripe.api_key = STRIPE_SECRET_KEY

# Database setup
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    ticket_text = Column(Text)
    label = Column(String)
    confidence = Column(Float)
    summary = Column(Text)
    api_key = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    customer_id = Column(String)
    rate_limit = Column(Integer, default=100)
    requests_today = Column(Integer, default=0)
    last_reset = Column(Date, default=datetime.utcnow().date)

Base.metadata.create_all(bind=engine)

# Models
class TicketRequest(BaseModel):
    ticket_text: str

class TicketResponse(BaseModel):
    label: str
    confidence: float
    summary: str

# Authentication
def verify_api_key(request: Request):
    api_key = request.headers.get("X-Api-Key")
    if api_key not in ALLOWED_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

# Rate limit per key
def check_rate_limit(api_key: str):
    db = SessionLocal()
    today = datetime.utcnow().date()
    api_key_obj = db.query(ApiKey).filter(ApiKey.key == api_key).first()
    if not api_key_obj:
        db.close()
        raise HTTPException(status_code=401, detail="API key not found")
    if api_key_obj.last_reset != today:
        api_key_obj.requests_today = 0
        api_key_obj.last_reset = today
    if api_key_obj.requests_today >= api_key_obj.rate_limit:
        db.close()
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    api_key_obj.requests_today += 1
    db.commit()
    db.close()

# Triage function with failover
def triage_ticket(ticket_text: str):
    prompt = f"Classify this ticket: {ticket_text}\n\nCategories: bug, feature_request, billing_issue, other\n\nProvide JSON: {{'label': '...', 'confidence': 0.0-1.0, 'summary': '...'}}\n\nStrict JSON only."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        result = json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        logging.warning(f"OpenAI failed: {e}, trying Anthropic")
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            result = json.loads(response.content[0].text.strip())
        except Exception as e2:
            logging.error(f"Anthropic failed: {e2}")
            result = {"label": "other", "confidence": 0.0, "summary": "Failed to classify"}
    return result

@app.post("/api/v1/triage", response_model=TicketResponse)
@limiter.limit("10/minute")
def triage(request: Request, ticket: TicketRequest, api_key: str = Depends(verify_api_key)):
    check_rate_limit(api_key)
    result = triage_ticket(ticket.ticket_text)
    # Log to DB
    db = SessionLocal()
    new_ticket = Ticket(
        ticket_text=ticket.ticket_text,
        label=result['label'],
        confidence=result['confidence'],
        summary=result['summary'],
        api_key=api_key
    )
    db.add(new_ticket)
    db.commit()
    db.close()
    return result

@app.get("/api/v1/recent")
def get_recent(api_key: str = Depends(verify_api_key)):
    db = SessionLocal()
    tickets = db.query(Ticket).filter(Ticket.api_key == api_key).order_by(Ticket.timestamp.desc()).limit(10).all()
    db.close()
    return [{"ticket_text": t.ticket_text, "label": t.label, "confidence": t.confidence, "summary": t.summary, "timestamp": t.timestamp.isoformat()} for t in tickets]

# Stripe webhook
@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_id = session['customer']
        # Generate API key and store
        api_key = f"key_{customer_id}"
        db = SessionLocal()
        existing = db.query(ApiKey).filter(ApiKey.key == api_key).first()
        if not existing:
            new_key = ApiKey(key=api_key, customer_id=customer_id)
            db.add(new_key)
        db.commit()
        db.close()
        # TODO: Send API key to customer email

    return {"status": "success"}

# Webhook for integrations
@app.post("/webhook/{provider}")
async def integration_webhook(provider: str, request: Request):
    data = await request.json()
    # Process webhook data, e.g., extract ticket and triage
    ticket_text = data.get("ticket_text", "")
    if ticket_text:
        result = triage_ticket(ticket_text)
        # Log or route based on label
        logging.info(f"Webhook from {provider}: {result}")
    return {"status": "processed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)