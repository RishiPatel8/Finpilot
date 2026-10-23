from typing import Optional, List, Dict
from decimal import Decimal
from pydantic import BaseModel, Field


class TaxCalculationInput(BaseModel):
    assessment_year: str = Field(default="2025-26", description="AY 2025-26 (FY 2024-25) or AY 2024-25 (FY 2023-24)")
    taxpayer_type: str = Field(default="salaried", description="salaried, freelancer, business_owner, senior_citizen")
    gross_annual_salary: Decimal = Field(default=Decimal("0.00"))
    business_turnover: Decimal = Field(default=Decimal("0.00"), description="For 44AD/44ADA")
    presumptive_profit_pct: Optional[Decimal] = Field(default=None, description="50% for 44ADA or 6%/8% for 44AD")
    other_income: Decimal = Field(default=Decimal("0.00"), description="Interest, dividend, capital gains, etc.")
    
    # Old Regime Deductions
    hra_exemption: Decimal = Field(default=Decimal("0.00"))
    section_80c: Decimal = Field(default=Decimal("0.00"), description="Max 1,50,000 (PPF, EPF, ELSS, etc.)")
    section_80d: Decimal = Field(default=Decimal("0.00"), description="Health Insurance (Self/Parents)")
    section_80ccd_1b: Decimal = Field(default=Decimal("0.00"), description="NPS employee contribution up to 50,000")
    section_80ccd_2: Decimal = Field(default=Decimal("0.00"), description="Employer NPS contribution (valid in both regimes)")
    home_loan_interest_24b: Decimal = Field(default=Decimal("0.00"), description="Self-occupied home loan interest (Max 2,00,000)")
    other_deductions_80tta_80g: Decimal = Field(default=Decimal("0.00"))


class SlabCalculation(BaseModel):
    slab_range: str
    taxable_in_slab: Decimal
    rate_pct: Decimal
    tax_amount: Decimal


class RegimeTaxBreakdown(BaseModel):
    regime: str  # "new" or "old"
    assessment_year: str
    gross_total_income: Decimal
    standard_deduction: Decimal
    allowed_deductions: Dict[str, Decimal]
    total_deductions: Decimal
    taxable_income: Decimal
    slab_details: List[SlabCalculation]
    tax_on_income: Decimal
    rebate_87a: Decimal
    marginal_relief: Decimal
    tax_after_rebate: Decimal
    surcharge: Decimal
    health_and_education_cess: Decimal
    total_tax_liability: Decimal
    effective_tax_rate_pct: float
    official_citations: List[str]


class TaxComparisonResponse(BaseModel):
    assessment_year: str
    taxpayer_type: str
    recommended_regime: str  # "new" or "old"
    tax_savings: Decimal
    explanation: str
    new_regime: RegimeTaxBreakdown
    old_regime: RegimeTaxBreakdown
    missing_inputs_note: Optional[str] = None
