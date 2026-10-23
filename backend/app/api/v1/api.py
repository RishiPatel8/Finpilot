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
    scenarios,
    liabilities,
    bank
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(profile.router, prefix="/profile", tags=["Financial Profile"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions & CSV Import"])
api_router.include_router(liabilities.router, prefix="/liabilities", tags=["Debt & Liabilities"])
api_router.include_router(tax.router, prefix="/tax", tags=["Indian Tax Engine"])
api_router.include_router(investments.router, prefix="/investments", tags=["Investments & Liquid vs Bonds"])
api_router.include_router(goals.router, prefix="/goals", tags=["Financial Goals"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["Financial Decision Simulator"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["AI Assistant & RAG"])
api_router.include_router(bank.router, prefix="/bank", tags=["Bank Connectivity & Account Aggregator"])
api_router.include_router(demo.router, prefix="/demo", tags=["Demo Data"])
