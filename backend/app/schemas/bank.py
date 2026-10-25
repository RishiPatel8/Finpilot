from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ConsentInitiateRequest(BaseModel):
    phone_number: str = Field(..., description="User 10-digit mobile number linked to bank account")
    fip_ids: Optional[List[str]] = Field(default=None, description="List of bank FIP identifiers")
    validity_days: int = Field(default=180, description="Validity of consent in days")


class ConsentInitiateResponse(BaseModel):
    id: str
    consent_handle: str
    provider: str
    status: str
    redirect_url: str
    valid_from: datetime
    valid_to: datetime
    mode: str


class ConsentStatusResponse(BaseModel):
    id: str
    consent_handle: str
    consent_id: Optional[str] = None
    provider: str
    status: str
    valid_to: datetime
    fip_ids: Optional[List[str]] = None


class ConsentCallbackRequest(BaseModel):
    consent_handle: str = Field(..., description="Consent handle returned by the Account Aggregator")
    status: Optional[str] = Field(default=None, description="Reported status from query parameters (e.g. ACCEPT, REJECT, APPROVED)")
    error: Optional[str] = Field(default=None, description="Error code or error description if consent was rejected or failed")


class ConsentCallbackResponse(BaseModel):
    consent_id: str
    consent_handle: str
    provider: str
    status: str
    message: str
    accounts_linked: int
    accounts: List["BankAccountResponse"] = []


class BankAccountResponse(BaseModel):
    id: str
    institution_name: str
    account_number_masked: str
    account_type: str
    ifsc_code: str
    currency: str
    current_balance: float
    balance_type: str
    balance_timestamp: datetime
    sync_status: str
    last_synced_at: Optional[datetime] = None


class SyncResponse(BaseModel):
    account_id: str
    institution_name: str
    synced_count: int
    current_balance: float
    balance_timestamp: datetime
    sync_status: str
    message: str


class BankSyncLogResponse(BaseModel):
    id: str
    account_id: str
    sync_status: str
    records_synced: int
    error_message: Optional[str] = None
    synced_at: datetime


class ReBITNotifier(BaseModel):
    type: str = Field(default="AA", description="Notifier entity type, typically AA")
    id: str = Field(..., description="Notifier entity identifier, e.g. finvu-aa")


class ReBITConsentStatusNotification(BaseModel):
    consentId: Optional[str] = Field(default=None, description="Account Aggregator consent ID")
    consentHandle: str = Field(..., description="Consent handle identifier")
    consentStatus: str = Field(..., description="Status: ACTIVE, REJECTED, REVOKED, EXPIRED, PAUSED")


class ReBITFIAccountStatus(BaseModel):
    linkRefNumber: Optional[str] = None
    FIStatus: Optional[str] = None


class ReBITFIFIPResponse(BaseModel):
    fipId: Optional[str] = None
    accounts: Optional[List[ReBITFIAccountStatus]] = None


class ReBITFIStatusNotification(BaseModel):
    sessionId: str = Field(..., description="Financial Information session identifier")
    sessionStatus: str = Field(..., description="Session status: COMPLETED, READY, FAILED, PARTIAL")
    FIStatusResponse: Optional[List[ReBITFIFIPResponse]] = None


class ReBITWebhookPayload(BaseModel):
    ver: str = Field(default="2.0.0", description="ReBIT schema version")
    timestamp: str = Field(..., description="ISO 8601 event timestamp")
    txnid: str = Field(..., description="Unique transaction ID for tracking & idempotency")
    Notifier: ReBITNotifier = Field(..., description="Notifier metadata")
    ConsentStatusNotification: Optional[ReBITConsentStatusNotification] = Field(default=None, description="Consent status event")
    FIStatusNotification: Optional[ReBITFIStatusNotification] = Field(default=None, description="FI data status event")


class ReBITWebhookResponse(BaseModel):
    ver: str = Field(default="2.0.0")
    timestamp: str
    txnid: str
    response: str = Field(default="OK")
