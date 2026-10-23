from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.models.user import User
from app.models.financial import TaxRecord
from app.schemas.tax import TaxCalculationInput, TaxComparisonResponse
from app.finance.tax.engine import IndianTaxEngine
from app.api.deps import get_optional_current_user

router = APIRouter()


@router.post("/compare", response_model=TaxComparisonResponse)
def compare_tax_regimes(
    tax_in: TaxCalculationInput,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    comparison = IndianTaxEngine.compare_regimes(tax_in)

    # If authenticated, persist the calculation record for user's history
    if current_user:
        try:
            record = TaxRecord(
                user_id=current_user.id,
                assessment_year=tax_in.assessment_year,
                gross_income=tax_in.gross_annual_salary + tax_in.other_income,
                total_deductions=comparison.old_regime.total_deductions,
                regime=comparison.recommended_regime,
                calculated_tax=(
                    comparison.new_regime.total_tax_liability
                    if comparison.recommended_regime == "new"
                    else comparison.old_regime.total_tax_liability
                ),
                calculation_details=comparison.model_dump(mode="json")
            )
            db.add(record)
            db.commit()
        except Exception:
            db.rollback()

    return comparison
