from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.db.session import engine, Base
import app.models  # ensure all models are registered
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("finpilot")

# Ensure database tables exist and update schema
try:
    Base.metadata.create_all(bind=engine)
    # Check SQLite schema to ensure newly added columns are present
    if engine.url.drivername.startswith("sqlite"):
        with engine.connect() as conn:
            result = conn.exec_driver_sql("PRAGMA table_info(transactions);")
            existing_cols = {row[1] for row in result.fetchall()}
            cols_to_add = [
                ("value_date", "DATE"),
                ("reference_number", "VARCHAR(128)"),
                ("balance_after", "NUMERIC(14, 2)"),
                ("source_file", "VARCHAR(255)"),
                ("source_row", "INTEGER"),
                ("batch_id", "VARCHAR(36)"),
                ("account_mask", "VARCHAR(30)"),
                ("raw_type", "VARCHAR(30)"),
            ]
            for col_name, col_type in cols_to_add:
                if col_name not in existing_cols:
                    conn.exec_driver_sql(f"ALTER TABLE transactions ADD COLUMN {col_name} {col_type};")

            liab_result = conn.exec_driver_sql("PRAGMA table_info(liabilities);")
            existing_liab_cols = {row[1] for row in liab_result.fetchall()}
            liab_cols_to_add = [
                ("debt_type", "VARCHAR(32) DEFAULT 'payable'"),
                ("counterparty", "VARCHAR(255)"),
                ("interest_period", "VARCHAR(20) DEFAULT 'annual'"),
                ("status", "VARCHAR(32) DEFAULT 'active'"),
                ("loan_date", "DATE"),
                ("due_date", "DATE"),
                ("repayment_frequency", "VARCHAR(32) DEFAULT 'monthly'"),
                ("notes", "TEXT"),
            ]
            for col_name, col_type in liab_cols_to_add:
                if col_name not in existing_liab_cols:
                    conn.exec_driver_sql(f"ALTER TABLE liabilities ADD COLUMN {col_name} {col_type};")

            conn.commit()
    logger.info("Database tables and schema initialized successfully.")
except Exception as e:
    logger.warning(f"Database table initialization deferred: {e}")

# Startup provider logging (Never log credentials or secrets)
selected_bank_provider = getattr(settings, "BANK_PROVIDER", "sandbox").lower().strip()
logger.info(f"Account Aggregator Bank Provider initialized: {selected_bank_provider.upper()}")
if selected_bank_provider == "finvu":
    if not getattr(settings, "BANK_FINVU_CLIENT_ID", "") or not getattr(settings, "BANK_FINVU_CLIENT_SECRET", ""):
        logger.warning(
            "Finvu AA selected (BANK_PROVIDER=finvu) but BANK_FINVU_CLIENT_ID or BANK_FINVU_CLIENT_SECRET is missing. "
            "Consent requests will fail with BankProviderConfigurationError until credentials are configured in backend/.env."
        )

app = FastAPI(
    title=settings.APP_NAME,
    description="Explainable personal finance intelligence platform for Indian users.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Root health endpoint
@app.get("/health", tags=["Health"])
def root_health():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

# Mount API V1
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."}
    )
