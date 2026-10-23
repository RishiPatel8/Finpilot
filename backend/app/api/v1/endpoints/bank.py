from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.bank import BankConsent, BankAccount, BankSyncLog
from app.models.financial import Transaction
from app.schemas.bank import (
    ConsentInitiateRequest,
    ConsentInitiateResponse,
    ConsentStatusResponse,
    BankAccountResponse,
    SyncResponse,
    BankSyncLogResponse,
)
from app.bank.adapter import get_bank_adapter
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/consent/initiate", response_model=ConsentInitiateResponse)
def initiate_consent(
    req: ConsentInitiateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    adapter = get_bank_adapter()
    result = adapter.create_consent(
        user_id=current_user.id,
        phone_number=req.phone_number,
        fip_ids=req.fip_ids or ["FIP_HDFC", "FIP_ICICI"],
        validity_days=req.validity_days
    )

    consent = BankConsent(
        user_id=current_user.id,
        consent_handle=result["consent_handle"],
        provider=result["provider"],
        status="PENDING",
        fip_ids=result["fip_ids"],
        fi_types=result["fi_types"],
        valid_from=datetime.fromisoformat(result["valid_from"]),
        valid_to=datetime.fromisoformat(result["valid_to"]),
        fetch_frequency=result["fetch_frequency"]
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)

    return ConsentInitiateResponse(
        id=consent.id,
        consent_handle=consent.consent_handle,
        provider=consent.provider,
        status=consent.status,
        redirect_url=result["redirect_url"],
        valid_from=consent.valid_from,
        valid_to=consent.valid_to,
        mode=result["mode"]
    )


@router.get("/consent/{consent_id}", response_model=ConsentStatusResponse)
def get_consent_status(
    consent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    consent = db.query(BankConsent).filter(
        BankConsent.id == consent_id,
        BankConsent.user_id == current_user.id
    ).first()
    if not consent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent record not found")

    return ConsentStatusResponse(
        id=consent.id,
        consent_handle=consent.consent_handle,
        consent_id=consent.consent_id,
        provider=consent.provider,
        status=consent.status,
        valid_to=consent.valid_to,
        fip_ids=consent.fip_ids
    )


@router.post("/consent/{consent_id}/approve", response_model=List[BankAccountResponse])
def approve_consent(
    consent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    consent = db.query(BankConsent).filter(
        BankConsent.id == consent_id,
        BankConsent.user_id == current_user.id
    ).first()
    if not consent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent record not found")

    adapter = get_bank_adapter()
    status_res = adapter.get_consent_status(consent.consent_handle)
    consent.status = "ACTIVE"
    consent.consent_id = status_res.get("consent_id", consent.consent_handle)
    db.commit()

    # Discover and link accounts
    raw_accounts = adapter.fetch_accounts(consent.consent_id)
    linked_accounts = []

    for acc_data in raw_accounts:
        existing = db.query(BankAccount).filter(
            BankAccount.user_id == current_user.id,
            BankAccount.account_number_masked == acc_data["account_number_masked"],
            BankAccount.institution_name == acc_data["institution_name"]
        ).first()

        if not existing:
            new_acc = BankAccount(
                user_id=current_user.id,
                consent_id=consent.id,
                institution_name=acc_data["institution_name"],
                account_number_masked=acc_data["account_number_masked"],
                account_type=acc_data["account_type"],
                ifsc_code=acc_data["ifsc_code"],
                currency=acc_data["currency"],
                current_balance=acc_data["current_balance"],
                balance_type=acc_data["balance_type"],
                balance_timestamp=datetime.fromisoformat(acc_data["balance_timestamp"]),
                sync_status="synced",
                last_synced_at=datetime.now(timezone.utc)
            )
            db.add(new_acc)
            db.commit()
            db.refresh(new_acc)
            linked_accounts.append(new_acc)

            # Perform initial transaction sync for the account
            sync_data = adapter.sync_transactions(
                account_id=new_acc.id,
                account_number_masked=new_acc.account_number_masked,
                institution_name=new_acc.institution_name
            )
            for tx in sync_data.get("transactions", []):
                dup = db.query(Transaction).filter(
                    Transaction.user_id == current_user.id,
                    Transaction.provider_txn_ref == tx["provider_txn_ref"]
                ).first()
                if not dup:
                    t = Transaction(
                        user_id=current_user.id,
                        bank_account_id=new_acc.id,
                        date=tx["date"],
                        amount=tx["amount"],
                        type=tx["type"],
                        category=tx["category"],
                        description=tx["description"],
                        source="bank_sync",
                        provider_txn_ref=tx["provider_txn_ref"],
                        is_internal_transfer=tx["is_internal_transfer"]
                    )
                    db.add(t)

            log = BankSyncLog(
                user_id=current_user.id,
                account_id=new_acc.id,
                sync_status="SUCCESS",
                records_synced=len(sync_data.get("transactions", [])),
                error_message=None
            )
            db.add(log)
            db.commit()
        else:
            existing.consent_id = consent.id
            existing.sync_status = "synced"
            db.commit()
            linked_accounts.append(existing)

    return [
        BankAccountResponse(
            id=a.id,
            institution_name=a.institution_name,
            account_number_masked=a.account_number_masked,
            account_type=a.account_type,
            ifsc_code=a.ifsc_code,
            currency=a.currency,
            current_balance=float(a.current_balance),
            balance_type=a.balance_type,
            balance_timestamp=a.balance_timestamp,
            sync_status=a.sync_status,
            last_synced_at=a.last_synced_at
        )
        for a in linked_accounts
    ]


@router.post("/consent/{consent_id}/revoke", status_code=status.HTTP_200_OK)
def revoke_consent(
    consent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    consent = db.query(BankConsent).filter(
        BankConsent.id == consent_id,
        BankConsent.user_id == current_user.id
    ).first()
    if not consent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent record not found")

    adapter = get_bank_adapter()
    adapter.revoke_consent(consent.consent_id or consent.consent_handle)

    consent.status = "REVOKED"
    # Mark linked accounts as stale
    for acc in consent.accounts:
        acc.sync_status = "stale"
    db.commit()

    return {"message": "Consent successfully revoked. Background synchronization disabled.", "consent_id": consent_id}


@router.get("/accounts", response_model=List[BankAccountResponse])
def get_linked_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    accounts = db.query(BankAccount).filter(BankAccount.user_id == current_user.id).all()
    return [
        BankAccountResponse(
            id=a.id,
            institution_name=a.institution_name,
            account_number_masked=a.account_number_masked,
            account_type=a.account_type,
            ifsc_code=a.ifsc_code,
            currency=a.currency,
            current_balance=float(a.current_balance),
            balance_type=a.balance_type,
            balance_timestamp=a.balance_timestamp,
            sync_status=a.sync_status,
            last_synced_at=a.last_synced_at
        )
        for a in accounts
    ]


@router.post("/accounts/{account_id}/sync", response_model=SyncResponse)
def sync_account_transactions(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(BankAccount).filter(
        BankAccount.id == account_id,
        BankAccount.user_id == current_user.id
    ).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bank account not found")

    adapter = get_bank_adapter()
    sync_result = adapter.sync_transactions(
        account_id=account.id,
        account_number_masked=account.account_number_masked,
        institution_name=account.institution_name
    )

    imported_count = 0
    for tx in sync_result.get("transactions", []):
        existing_tx = db.query(Transaction).filter(
            Transaction.user_id == current_user.id,
            Transaction.provider_txn_ref == tx["provider_txn_ref"]
        ).first()
        if not existing_tx:
            t = Transaction(
                user_id=current_user.id,
                bank_account_id=account.id,
                date=tx["date"],
                amount=tx["amount"],
                type=tx["type"],
                category=tx["category"],
                description=tx["description"],
                source="bank_sync",
                provider_txn_ref=tx["provider_txn_ref"],
                is_internal_transfer=tx["is_internal_transfer"]
            )
            db.add(t)
            imported_count += 1

    # Update balance
    bal_res = adapter.get_balance(account.id, account.institution_name)
    account.current_balance = bal_res["current_balance"]
    account.balance_timestamp = datetime.fromisoformat(bal_res["balance_timestamp"])
    account.sync_status = "synced"
    account.last_synced_at = datetime.now(timezone.utc)

    # Log sync
    log = BankSyncLog(
        user_id=current_user.id,
        account_id=account.id,
        sync_status="SUCCESS",
        records_synced=imported_count,
        error_message=None
    )
    db.add(log)
    db.commit()

    return SyncResponse(
        account_id=account.id,
        institution_name=account.institution_name,
        synced_count=imported_count,
        current_balance=float(account.current_balance),
        balance_timestamp=account.balance_timestamp,
        sync_status="synced",
        message=f"Synchronized {imported_count} new transactions. Current balance updated."
    )


@router.get("/logs", response_model=List[BankSyncLogResponse])
def get_sync_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logs = db.query(BankSyncLog).filter(BankSyncLog.user_id == current_user.id).order_by(BankSyncLog.synced_at.desc()).limit(20).all()
    return [
        BankSyncLogResponse(
            id=l.id,
            account_id=l.account_id,
            sync_status=l.sync_status,
            records_synced=l.records_synced,
            error_message=l.error_message,
            synced_at=l.synced_at
        )
        for l in logs
    ]
