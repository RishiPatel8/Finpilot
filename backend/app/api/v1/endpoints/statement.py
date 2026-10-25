from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from decimal import Decimal

from app.db.session import get_db
from app.models.user import User
from app.models.financial import StatementImportBatch, Transaction, FinancialProfile
from app.schemas.financial import StatementImportConfirmRequest, StatementBatchResponse
from app.finance.statement.pipeline import StatementPipeline
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/preview", status_code=status.HTTP_200_OK)
async def preview_statement_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Parses and analyzes an uploaded bank statement (CSV, XLSX, PDF).
    Returns normalized transactions, metadata, warnings, and duplicate flags.
    Never logs or persists raw statement files.
    """
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded statement file is empty."
        )

    if len(content) > 15 * 1024 * 1024:  # 15 MB limit
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the 15MB limit. Please upload a compressed or shorter period statement."
        )

    result = StatementPipeline.process_file_upload(
        file_bytes=content,
        filename=file.filename or "statement",
        user=current_user,
        db=db
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result.get("error", "Failed to extract valid transactions from statement.")
        )

    return result


@router.post("/confirm", status_code=status.HTTP_201_CREATED)
def confirm_statement_import(
    req: StatementImportConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Atomically persists approved transactions, creates an import batch audit record,
    reconciles bank balances, updates financial run-rates, and verifies database persistence.
    """
    raw_txns = [t.model_dump() for t in req.transactions]
    res = StatementPipeline.confirm_import(
        user=current_user,
        transactions_data=raw_txns,
        filename=req.filename,
        file_format=req.file_format,
        metadata=req.metadata,
        db=db
    )

    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("message", "Could not persist transactions.")
        )

    return res


@router.get("/history", response_model=List[StatementBatchResponse])
def get_statement_batches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns audit history of all statement import batches for the authenticated user.
    """
    batches = db.query(StatementImportBatch).filter(
        StatementImportBatch.user_id == current_user.id
    ).order_by(StatementImportBatch.created_at.desc()).all()

    return [StatementBatchResponse.model_validate(b) for b in batches]


@router.delete("/batch/{batch_id}", status_code=status.HTTP_200_OK)
def rollback_statement_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Safely rolls back an imported statement batch, deleting associated transactions
    and recalculating financial run-rates.
    """
    batch = db.query(StatementImportBatch).filter(
        StatementImportBatch.id == batch_id,
        StatementImportBatch.user_id == current_user.id
    ).first()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement import batch not found."
        )

    # Delete transactions associated with this batch
    deleted_count = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.batch_id == batch_id
    ).delete()

    db.delete(batch)

    # Recalculate profile monthly run-rates from remaining verified transactions
    txns = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.is_internal_transfer == False
    ).all()

    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == current_user.id).first()
    if profile:
        if txns:
            dates = [t.date for t in txns]
            min_d = min(dates)
            max_d = max(dates)
            days = max(30, (max_d - min_d).days + 1)
            months = Decimal(str(days / 30.0))
            cr_sum = sum((t.amount for t in txns if t.type == "income"), Decimal("0.00"))
            dr_sum = sum((t.amount for t in txns if t.type == "expense"), Decimal("0.00"))
            profile.monthly_income = (cr_sum / months).quantize(Decimal("1.00"))
            profile.monthly_expenses = (dr_sum / months).quantize(Decimal("1.00"))
        else:
            profile.monthly_income = Decimal("0.00")
            profile.monthly_expenses = Decimal("0.00")

    db.commit()

    return {
        "success": True,
        "message": f"Successfully rolled back batch {batch_id}. Deleted {deleted_count} transactions.",
        "deleted_count": deleted_count
    }
