from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.recurring import (
    RecurringTransactionCreate,
    RecurringTransactionUpdate,
    RecurringTransactionConfirmRequest,
    RecurringTransactionDismissRequest,
    RecurringTransactionResponse,
    UpcomingSummary,
    RecurringSummary,
)
from app.finance.recurring.service import RecurringTransactionService


router = APIRouter()


@router.get("", response_model=List[RecurringTransactionResponse])
def list_recurring_transactions(
    status: Optional[str] = Query(None, pattern="^(detected|confirmed|paused|dismissed|cancelled)$"),
    transaction_type: Optional[str] = Query(None, pattern="^(income|expense)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns user-scoped recurring transactions, optionally filtered by status or type.
    """
    return RecurringTransactionService.list_recurring(
        user=current_user,
        db=db,
        status_filter=status,
        txn_type=transaction_type
    )


@router.get("/detections", response_model=List[RecurringTransactionResponse])
def get_recurring_detections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Runs intelligence detection, syncs with database records,
    and returns pending unconfirmed/unreviewed recurring items.
    """
    return RecurringTransactionService.sync_and_get_detections(user=current_user, db=db)


@router.get("/summary", response_model=RecurringSummary)
def get_recurring_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns monthly recurring commitment summaries, active counts, and next upcoming dates.
    """
    return RecurringTransactionService.get_recurring_summary(user=current_user, db=db)


@router.get("/upcoming", response_model=UpcomingSummary)
def get_upcoming_recurring(
    horizon_days: int = Query(30, ge=1, le=180),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculates expected occurrences over the specified horizon (default 30 days)
    for active confirmed recurring obligations.
    """
    return RecurringTransactionService.get_upcoming_occurrences(
        user=current_user,
        db=db,
        horizon_days=horizon_days
    )


@router.get("/{item_id}", response_model=RecurringTransactionResponse)
def get_recurring_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves a single recurring item by ID, scoped to authenticated user.
    """
    return RecurringTransactionService.get_by_id(user=current_user, db=db, item_id=item_id)


@router.post("", response_model=RecurringTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_recurring_transaction(
    data: RecurringTransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually creates a new confirmed recurring transaction.
    """
    return RecurringTransactionService.create_recurring(user=current_user, db=db, data=data)


@router.post("/{item_id}/confirm", response_model=RecurringTransactionResponse)
def confirm_recurring_transaction(
    item_id: str,
    data: Optional[RecurringTransactionConfirmRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirms an AI-detected recurring transaction into an active user-controlled record.
    Allows optional editing of amounts, dates, or frequencies prior to confirmation.
    """
    return RecurringTransactionService.confirm_recurring(
        user=current_user,
        db=db,
        item_id=item_id,
        data=data
    )


@router.patch("/{item_id}", response_model=RecurringTransactionResponse)
def update_recurring_transaction(
    item_id: str,
    data: RecurringTransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates details (name, amount, frequency, next date, notes) of an existing recurring item.
    """
    return RecurringTransactionService.update_recurring(
        user=current_user,
        db=db,
        item_id=item_id,
        data=data
    )


@router.post("/{item_id}/dismiss", response_model=RecurringTransactionResponse)
def dismiss_recurring_transaction(
    item_id: str,
    data: Optional[RecurringTransactionDismissRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Dismisses a detected recurring transaction so it stops appearing in review queues.
    Accepts optional user feedback for intelligence engine learning.
    """
    return RecurringTransactionService.dismiss_recurring(
        user=current_user,
        db=db,
        item_id=item_id,
        dismiss_data=data
    )


@router.post("/{item_id}/pause", response_model=RecurringTransactionResponse)
def pause_recurring_transaction(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pauses an active recurring item (e.g., temporary subscription pause).
    """
    return RecurringTransactionService.pause_recurring(user=current_user, db=db, item_id=item_id)


@router.post("/{item_id}/reactivate", response_model=RecurringTransactionResponse)
def reactivate_recurring_transaction(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reactivates a paused recurring item.
    """
    return RecurringTransactionService.reactivate_recurring(user=current_user, db=db, item_id=item_id)


@router.post("/{item_id}/cancel", response_model=RecurringTransactionResponse)
def cancel_recurring_transaction(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marks a recurring item as permanently cancelled, retaining historical reference.
    """
    return RecurringTransactionService.cancel_recurring(user=current_user, db=db, item_id=item_id)
