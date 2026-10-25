from typing import List
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.bank import BankConsent, BankAccount, BankSyncLog, BankWebhookLog
from app.models.financial import Transaction
from app.schemas.bank import (
    ConsentInitiateRequest,
    ConsentInitiateResponse,
    ConsentStatusResponse,
    ConsentCallbackRequest,
    ConsentCallbackResponse,
    BankAccountResponse,
    SyncResponse,
    BankSyncLogResponse,
    ReBITWebhookPayload,
    ReBITWebhookResponse,
)
from app.bank.adapter import get_bank_adapter, BankProviderConfigurationError
from app.bank.security import verify_bank_webhook
from app.api.deps import get_current_user

logger = logging.getLogger("finpilot.bank")

router = APIRouter()


@router.post("/consent/initiate", response_model=ConsentInitiateResponse)
def initiate_consent(
    req: ConsentInitiateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        adapter = get_bank_adapter()
        result = adapter.create_consent(
            user_id=current_user.id,
            phone_number=req.phone_number,
            fip_ids=req.fip_ids or ["FIP_HDFC", "FIP_ICICI"],
            validity_days=req.validity_days
        )
    except BankProviderConfigurationError as e:
        logger.error(f"Bank provider configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Bank aggregator provider error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
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


def _link_and_sync_discovered_accounts(
    consent: BankConsent,
    current_user: User,
    db: Session,
    adapter
) -> List[BankAccount]:
    """Helper to discover and link accounts for an active consent with initial transaction sync."""
    raw_accounts = adapter.fetch_accounts(consent.consent_id or consent.consent_handle)
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

    return linked_accounts


@router.get("/consent/by-handle/{consent_handle}", response_model=ConsentStatusResponse)
def get_consent_by_handle(
    consent_handle: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    consent = db.query(BankConsent).filter(
        BankConsent.consent_handle == consent_handle,
        BankConsent.user_id == current_user.id
    ).first()
    if not consent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent record not found for this handle")

    return ConsentStatusResponse(
        id=consent.id,
        consent_handle=consent.consent_handle,
        consent_id=consent.consent_id,
        provider=consent.provider,
        status=consent.status,
        valid_to=consent.valid_to,
        fip_ids=consent.fip_ids
    )


@router.post("/consent/callback", response_model=ConsentCallbackResponse)
def handle_consent_callback(
    req: ConsentCallbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Handles the Account Aggregator (Finvu / Setu / Sandbox) redirect callback safely.
    
    Security & State Preservation:
    Query parameters alone (such as `status=ACCEPT`) are NEVER trusted as proof of approval.
    The backend looks up the user's consent record by consent_handle, and queries the
    authoritative Account Aggregator adapter directly for real-time status.
    """
    consent = db.query(BankConsent).filter(
        BankConsent.consent_handle == req.consent_handle,
        BankConsent.user_id == current_user.id
    ).first()
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent record matching this handle was not found for the authenticated user."
        )

    # 1. Handle explicit user cancellation / decline from redirect
    if req.status and req.status.upper() in ["REJECT", "REJECTED", "FAILED", "DECLINED", "CANCELLED"]:
        consent.status = "REJECTED"
        db.commit()
        return ConsentCallbackResponse(
            consent_id=consent.id,
            consent_handle=consent.consent_handle,
            provider=consent.provider,
            status="REJECTED",
            message="Account Aggregator consent was declined or cancelled. No bank accounts were linked.",
            accounts_linked=0,
            accounts=[]
        )

    # 2. Authoritative Verification: Call Account Aggregator Adapter directly
    try:
        adapter = get_bank_adapter()
        status_res = adapter.get_consent_status(consent.consent_handle)
    except BankProviderConfigurationError as e:
        logger.error(f"Bank provider configuration error during callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    verified_status = status_res.get("status", "PENDING").upper()

    # Reject if provider does not confirm active state (protects against query param spoofing)
    if verified_status not in ["ACTIVE", "APPROVED", "SUCCESS"]:
        consent.status = verified_status if verified_status in ["REJECTED", "EXPIRED", "REVOKED"] else "FAILED"
        db.commit()
        return ConsentCallbackResponse(
            consent_id=consent.id,
            consent_handle=consent.consent_handle,
            provider=consent.provider,
            status=consent.status,
            message=f"Consent verification failed. Authoritative Account Aggregator status is {consent.status}.",
            accounts_linked=0,
            accounts=[]
        )

    # 3. Provider confirmed ACTIVE: Update DB record
    consent.status = "ACTIVE"
    consent.consent_id = status_res.get("consent_id", consent.consent_handle)
    db.commit()

    # 4. Discover accounts and perform initial transaction sync
    linked = _link_and_sync_discovered_accounts(consent, current_user, db, adapter)

    return ConsentCallbackResponse(
        consent_id=consent.id,
        consent_handle=consent.consent_handle,
        provider=consent.provider,
        status="ACTIVE",
        message=f"Successfully verified consent with {consent.provider.title()} Account Aggregator. {len(linked)} accounts connected.",
        accounts_linked=len(linked),
        accounts=[
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
            for a in linked
        ]
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

    linked_accounts = _link_and_sync_discovered_accounts(consent, current_user, db, adapter)

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


async def _process_rebit_notification(
    request: Request,
    db: Session
) -> ReBITWebhookResponse:
    """
    Core ReBIT 2.0 / Finvu server-to-server webhook event processor.
    
    Security & Cryptographic Guarantees:
    1. Authenticates incoming webhook via ReBIT detached JWS ('x-jws-signature') or BANK_WEBHOOK_SECRET.
    2. Validates schema payload.
    3. Idempotently tracks events by unique 'txnid' to prevent duplicate processing on retries.
    4. Never trusts client claim of ACTIVE status without authoritative provider verification.
    5. Audits event lifecycle in BankWebhookLog without storing credentials or raw banking statements.
    """
    raw_body = await request.body()
    headers = dict(request.headers)

    # 1. Cryptographic signature and authentication check
    if not verify_bank_webhook(headers=headers, raw_body=raw_body):
        logger.warning("Rejected ReBIT webhook: invalid signature or authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing ReBIT webhook signature / authorization"
        )

    # 2. Parse JSON payload against ReBIT specification
    try:
        data = json.loads(raw_body.decode("utf-8"))
        payload = ReBITWebhookPayload.model_validate(data)
    except Exception as e:
        logger.warning(f"Malformed ReBIT webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed ReBIT webhook payload: {str(e)}"
        )

    # 3. Idempotency Check: check if txnid has already been processed
    existing_event = db.query(BankWebhookLog).filter(BankWebhookLog.txnid == payload.txnid).first()
    if existing_event:
        logger.info(f"Duplicate webhook event txnid: '{payload.txnid}' already processed. Returning OK.")
        return ReBITWebhookResponse(
            ver=payload.ver,
            timestamp=datetime.now(timezone.utc).isoformat(),
            txnid=payload.txnid,
            response="OK"
        )

    # 4. Handle ConsentStatusNotification (Lifecycle events: ACTIVE, REJECTED, REVOKED, EXPIRED)
    if payload.ConsentStatusNotification:
        c_notif = payload.ConsentStatusNotification
        consent_handle = c_notif.consentHandle
        consent_status = c_notif.consentStatus.upper()

        consent = db.query(BankConsent).filter(
            BankConsent.consent_handle == consent_handle
        ).first()

        if not consent:
            logger.warning(f"Webhook received for unknown consent handle: {consent_handle}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Consent record matching handle '{consent_handle}' was not found"
            )

        if consent_status == "ACTIVE":
            # Security Requirement: Authoritative check against provider API, do not trust notification claim blindly
            adapter = get_bank_adapter()
            status_res = adapter.get_consent_status(consent.consent_handle)
            verified_status = status_res.get("status", "PENDING").upper()

            if verified_status in ["ACTIVE", "APPROVED", "SUCCESS"]:
                consent.status = "ACTIVE"
                consent.consent_id = c_notif.consentId or status_res.get("consent_id", consent.consent_handle)
                db.commit()
                # Discover accounts and sync initial transactions for user
                _link_and_sync_discovered_accounts(consent, consent.user, db, adapter)
            else:
                consent.status = verified_status if verified_status in ["REJECTED", "EXPIRED", "REVOKED"] else "FAILED"
                db.commit()

        elif consent_status in ["REVOKED", "EXPIRED", "PAUSED"]:
            consent.status = consent_status
            for acc in consent.accounts:
                acc.sync_status = "stale"
            db.commit()

        elif consent_status in ["REJECTED", "FAILED"]:
            consent.status = "REJECTED"
            db.commit()

        # Log event for audit and idempotency
        log = BankWebhookLog(
            txnid=payload.txnid,
            event_type="CONSENT_STATUS",
            notifier_type=payload.Notifier.type,
            notifier_id=payload.Notifier.id,
            consent_handle=consent_handle,
            status=consent_status,
            processed="PROCESSED"
        )
        db.add(log)
        db.commit()

    # 5. Handle FIStatusNotification (Data flow events: COMPLETED, READY, FAILED)
    elif payload.FIStatusNotification:
        fi_notif = payload.FIStatusNotification
        session_id = fi_notif.sessionId
        session_status = fi_notif.sessionStatus.upper()

        log = BankWebhookLog(
            txnid=payload.txnid,
            event_type="FI_STATUS",
            notifier_type=payload.Notifier.type,
            notifier_id=payload.Notifier.id,
            consent_handle=session_id,
            status=session_status,
            processed="PROCESSED"
        )
        db.add(log)
        db.commit()

    return ReBITWebhookResponse(
        ver=payload.ver or "2.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        txnid=payload.txnid,
        response="OK"
    )


@router.post("/Consent/Notification", response_model=ReBITWebhookResponse)
async def handle_consent_notification(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    ReBIT 2.0 / Finvu official Consent/Notification server-to-server webhook endpoint.
    Notifies FIU when user grants, modifies, rejects, or revokes consent on AA portal.
    """
    return await _process_rebit_notification(request, db)


@router.post("/FI/Notification", response_model=ReBITWebhookResponse)
async def handle_fi_notification(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    ReBIT 2.0 / Finvu official FI/Notification server-to-server webhook endpoint.
    Notifies FIU when banking statements & financial information data are aggregated and ready.
    """
    return await _process_rebit_notification(request, db)


@router.post("/webhook", response_model=ReBITWebhookResponse)
async def handle_unified_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Unified webhook endpoint for Account Aggregator partner dashboards that require
    a single callback URL to route both Consent and FI notifications.
    """
    return await _process_rebit_notification(request, db)
