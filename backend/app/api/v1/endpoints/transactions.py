from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.financial import Transaction
from app.schemas.financial import (
    TransactionCreate,
    TransactionResponse,
    CSVImportPreviewResponse,
    CSVImportConfirmRequest
)
from app.finance.budget.engine import BudgetEngine
from app.api.deps import get_current_user

router = APIRouter()


@router.get("", response_model=List[TransactionResponse])
def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
    txn_type: Optional[str] = None
):
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    if txn_type:
        query = query.filter(Transaction.type == txn_type)
    txns = query.order_by(Transaction.date.desc(), Transaction.created_at.desc()).offset(offset).limit(limit).all()
    return [TransactionResponse.model_validate(t) for t in txns]


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    txn_in: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    txn = Transaction(
        user_id=current_user.id,
        date=txn_in.date,
        amount=txn_in.amount,
        type=txn_in.type,
        category=txn_in.category,
        description=txn_in.description,
        source=txn_in.source,
        is_recurring=txn_in.is_recurring
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return TransactionResponse.model_validate(txn)


@router.delete("/{txn_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    txn_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    txn = db.query(Transaction).filter(Transaction.id == txn_id, Transaction.user_id == current_user.id).first()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    db.delete(txn)
    db.commit()


@router.post("/import-csv/preview", response_model=CSVImportPreviewResponse)
async def preview_csv_import(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        content = await file.read()
        csv_text = content.decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to read CSV file: {str(e)}")

    # Fetch existing transaction signatures for user to detect duplicates
    existing = db.query(Transaction.date, Transaction.amount, Transaction.description).filter(
        Transaction.user_id == current_user.id
    ).all()
    existing_signatures = {f"{str(d)}|{float(a)}|{desc.lower()}" for d, a, desc in existing}

    preview_res = BudgetEngine.parse_csv_transactions(csv_text, existing_signatures)
    return preview_res


@router.post("/import-csv/confirm", response_model=List[TransactionResponse], status_code=status.HTTP_201_CREATED)
def confirm_csv_import(
    req: CSVImportConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    created_txns = []
    for t_in in req.transactions:
        t = Transaction(
            user_id=current_user.id,
            date=t_in.date,
            amount=t_in.amount,
            type=t_in.type,
            category=t_in.category,
            description=t_in.description,
            source="csv_import",
            is_recurring=t_in.is_recurring
        )
        db.add(t)
        created_txns.append(t)

    db.commit()
    for t in created_txns:
        db.refresh(t)
    return [TransactionResponse.model_validate(t) for t in created_txns]
