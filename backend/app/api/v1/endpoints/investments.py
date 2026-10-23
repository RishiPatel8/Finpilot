from fastapi import APIRouter
from app.schemas.investment import InvestmentCompareRequest, InvestmentCompareResponse
from app.finance.investments.engine import InvestmentEngine

router = APIRouter()


@router.post("/compare", response_model=InvestmentCompareResponse)
def compare_investments(req: InvestmentCompareRequest):
    return InvestmentEngine.compare_instruments(req)
