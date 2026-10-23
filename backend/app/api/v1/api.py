from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    profile,
    transactions,
    tax,
    investments,
    goals,
    dashboard,
    assistant,
    demo,
    scenarios
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(profile.router, prefix="/profile", tags=["Financial Profile"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions & CSV Import"])
api_router.include_router(tax.router, prefix="/tax", tags=["Indian Tax Engine"])
api_router.include_router(investments.router, prefix="/investments", tags=["Investments & Liquid vs Bonds"])
api_router.include_router(goals.router, prefix="/goals", tags=["Financial Goals"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["Financial Decision Simulator"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["AI Assistant & RAG"])
api_router.include_router(demo.router, prefix="/demo", tags=["Demo Data"])
