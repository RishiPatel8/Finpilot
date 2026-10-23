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
