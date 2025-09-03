from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import psutil
import time
from datetime import datetime

from ..database import get_db
from ..config import settings
from ..schemas import HealthCheck, MetricsResponse

router = APIRouter(prefix="/health", tags=["health"])

# Track application start time
START_TIME = time.time()


@router.get("/", response_model=HealthCheck)
async def health_check(db: Session = Depends(get_db)):
    """Basic health check endpoint"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    uptime = time.time() - START_TIME

    return HealthCheck(
        status="healthy" if db_status == "healthy" else "unhealthy",
        version=settings.version,
        uptime=f"{uptime:.2f}s",
        database=db_status
    )


@router.get("/detailed", response_model=HealthCheck)
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with system metrics"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # System metrics
    uptime = time.time() - START_TIME
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)

    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "version": settings.version,
        "uptime": f"{uptime:.2f}s",
        "database": db_status,
        "memory_usage": f"{memory.percent:.1f}%",
        "cpu_usage": f"{cpu_percent:.1f}%",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(db: Session = Depends(get_db)):
    """Application metrics endpoint"""
    try:
        # Get ticket counts
        total_tickets = db.execute("SELECT COUNT(*) FROM tickets").scalar()
        total_api_keys = db.execute("SELECT COUNT(*) FROM api_keys").scalar()

        # Calculate average processing time
        result = db.execute("SELECT AVG(processing_time) FROM tickets WHERE processing_time IS NOT NULL").scalar()
        avg_processing_time = float(result) if result else 0.0

        uptime_seconds = int(time.time() - START_TIME)

        # Memory usage
        memory = psutil.virtual_memory()

        return MetricsResponse(
            total_tickets=total_tickets or 0,
            total_api_keys=total_api_keys or 0,
            avg_processing_time=round(avg_processing_time, 3),
            uptime_seconds=uptime_seconds,
            memory_usage={
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            }
        )

    except Exception as e:
        return MetricsResponse(
            total_tickets=0,
            total_api_keys=0,
            avg_processing_time=0.0,
            uptime_seconds=int(time.time() - START_TIME),
            memory_usage={"error": str(e)}
        )


@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"status": "pong", "timestamp": datetime.utcnow().isoformat()}