from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "healthy"
    db_backend = "unknown"
    db_host = "local"
    db_name = None
    try:
        db.execute(text("SELECT 1"))
        if hasattr(db, "bind") and db.bind:
            db_backend = db.bind.dialect.name
            db_host = getattr(db.bind.url, "host", "local") or "local"
            db_name = getattr(db.bind.url, "database", None)
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "database_backend": db_backend,
        "database_host": db_host,
        "database_name": db_name,
        "version": "1.0.0"
    }
