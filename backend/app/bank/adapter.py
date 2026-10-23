from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, date, timedelta
import uuid
import logging
from app.core.config import settings

logger = logging.getLogger("finpilot.bank")


class BankProviderConfigurationError(Exception):
    """Raised when an external bank aggregator provider is not properly configured."""
    pass


class BaseBankAdapter(ABC):
    """
    Provider-independent interface for Indian Account Aggregator (AA) integrations.
    Supports consent initiation, account discovery, balance retrieval, and transaction sync.
    """

    @abstractmethod
    def create_consent(
        self,
        user_id: str,
        phone_number: str,
        fip_ids: List[str],
        validity_days: int = 180
    ) -> Dict[str, Any]:
        """Initiates a consent request with the Account Aggregator."""
        pass

    @abstractmethod
    def get_consent_status(self, consent_handle: str) -> Dict[str, Any]:
        """Checks the current status of a consent request."""
        pass

    @abstractmethod
    def fetch_accounts(self, consent_id: str) -> List[Dict[str, Any]]:
        """Discovers authorized bank accounts linked under the active consent."""
        pass

    @abstractmethod
    def sync_transactions(
        self,
        account_id: str,
        account_number_masked: str,
        institution_name: str,
        from_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Synchronizes transactions for a linked account with deduplication metadata."""
        pass

    @abstractmethod
    def get_balance(self, account_id: str, institution_name: str) -> Dict[str, Any]:
        """Retrieves provider-reported balance and timestamp."""
        pass

    @abstractmethod
    def revoke_consent(self, consent_id: str) -> bool:
        """Revokes active consent with the Account Aggregator."""
        pass


class SandboxAccountAggregatorAdapter(BaseBankAdapter):
    """
    Deterministic Sandbox Account Aggregator Adapter.
    Simulates the RBI Account Aggregator flow with realistic Indian banks,
    masked account numbers, statutory ReBIT schemas, and idempotent transactions.
    """

    SUPPORTED_FIPS = [
        {"id": "FIP_HDFC", "name": "HDFC Bank", "ifsc": "HDFC0001234"},
        {"id": "FIP_ICICI", "name": "ICICI Bank", "ifsc": "ICIC0000001"},
        {"id": "FIP_SBI", "name": "State Bank of India", "ifsc": "SBIN0000001"},
        {"id": "FIP_AXIS", "name": "Axis Bank", "ifsc": "UTIB0000001"},
    ]

    def create_consent(
        self,
        user_id: str,
        phone_number: str,
        fip_ids: List[str],
        validity_days: int = 180
    ) -> Dict[str, Any]:
        consent_handle = f"cnh_sandbox_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        valid_to = now + timedelta(days=validity_days)

        return {
            "consent_handle": consent_handle,
            "provider": "sandbox",
            "status": "PENDING",
            "fip_ids": fip_ids or ["FIP_HDFC", "FIP_ICICI"],
            "fi_types": ["DEPOSIT"],
            "valid_from": now.isoformat(),
            "valid_to": valid_to.isoformat(),
            "fetch_frequency": "DAILY",
            "redirect_url": f"/sandbox/aa-consent?handle={consent_handle}",
            "mode": "SANDBOX (Simulated Indian Account Aggregator)"
        }

    def get_consent_status(self, consent_handle: str) -> Dict[str, Any]:
        return {
            "consent_handle": consent_handle,
            "status": "ACTIVE",
            "consent_id": f"cst_sandbox_{consent_handle[-10:]}",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

    def fetch_accounts(self, consent_id: str) -> List[Dict[str, Any]]:
        return [
            {
                "institution_name": "HDFC Bank",
                "account_number_masked": "XXXX-XXXX-4921",
                "account_type": "savings",
                "ifsc_code": "HDFC0001234",
                "currency": "INR",
                "current_balance": 184500.00,
                "balance_type": "provider_reported",
                "balance_timestamp": datetime.now(timezone.utc).isoformat(),
                "sync_status": "synced"
            },
            {
                "institution_name": "ICICI Bank",
                "account_number_masked": "XXXX-XXXX-8834",
                "account_type": "savings",
                "ifsc_code": "ICIC0000001",
                "currency": "INR",
                "current_balance": 65200.00,
                "balance_type": "provider_reported",
                "balance_timestamp": datetime.now(timezone.utc).isoformat(),
                "sync_status": "synced"
            }
        ]

    def sync_transactions(
        self,
        account_id: str,
        account_number_masked: str,
        institution_name: str,
        from_date: Optional[date] = None
    ) -> Dict[str, Any]:
        today = date.today()
        # Generates deterministic, idempotent Indian transactions with stable provider_txn_ref
        sample_txns = []

        if "HDFC" in institution_name or "4921" in account_number_masked:
            sample_txns = [
                {
                    "provider_txn_ref": f"TXN_{account_id[-6:]}_{today.strftime('%Y%m')}_001",
                    "date": today - timedelta(days=2),
                    "amount": 125000.00,
                    "type": "income",
                    "category": "Income",
                    "description": "INFOSYS TECH / SALARY CREDIT / NEFT",
                    "source": "bank_sync",
                    "is_internal_transfer": False,
                },
                {
                    "provider_txn_ref": f"TXN_{account_id[-6:]}_{today.strftime('%Y%m')}_002",
                    "date": today - timedelta(days=3),
                    "amount": 2850.00,
                    "type": "expense",
                    "category": "Food",
                    "description": "BLINKIT GROCERY DELIVERY BLR",
                    "source": "bank_sync",
                    "is_internal_transfer": False,
                },
                {
                    "provider_txn_ref": f"TXN_{account_id[-6:]}_{today.strftime('%Y%m')}_003",
                    "date": today - timedelta(days=5),
                    "amount": 3400.00,
                    "type": "expense",
                    "category": "Transport",
                    "description": "HPCL FUEL STATION INDIRANAGAR",
                    "source": "bank_sync",
                    "is_internal_transfer": False,
                },
                {
                    "provider_txn_ref": f"TXN_{account_id[-6:]}_{today.strftime('%Y%m')}_004",
                    "date": today - timedelta(days=7),
                    "amount": 25000.00,
                    "type": "expense",
                    "category": "Investment",
                    "description": "TRANSFER TO ICICI SAVINGS (SELF)",
                    "source": "bank_sync",
                    "is_internal_transfer": True,  # Internal transfer flag
                },
                {
                    "provider_txn_ref": f"TXN_{account_id[-6:]}_{today.strftime('%Y%m')}_005",
                    "date": today - timedelta(days=9),
                    "amount": 1820.00,
                    "type": "expense",
                    "category": "Housing",
                    "description": "BESCOM ELECTRICITY BILL BBPS",
                    "source": "bank_sync",
                    "is_internal_transfer": False,
                }
            ]
        else:
            sample_txns = [
                {
                    "provider_txn_ref": f"TXN_{account_id[-6:]}_{today.strftime('%Y%m')}_011",
                    "date": today - timedelta(days=7),
                    "amount": 25000.00,
                    "type": "income",
                    "category": "Transfer",
                    "description": "TRANSFER FROM HDFC BANK (SELF)",
                    "source": "bank_sync",
                    "is_internal_transfer": True,  # Internal transfer flag
                },
                {
                    "provider_txn_ref": f"TXN_{account_id[-6:]}_{today.strftime('%Y%m')}_012",
                    "date": today - timedelta(days=4),
                    "amount": 10000.00,
                    "type": "expense",
                    "category": "Investment",
                    "description": "ZERODHA BROKING MUTUAL FUND SIP",
                    "source": "bank_sync",
                    "is_internal_transfer": False,
                }
            ]

        return {
            "account_id": account_id,
            "synced_count": len(sample_txns),
            "transactions": sample_txns,
            "sync_status": "SUCCESS",
            "synced_at": datetime.now(timezone.utc).isoformat()
        }

    def get_balance(self, account_id: str, institution_name: str) -> Dict[str, Any]:
        balance = 184500.00 if "HDFC" in institution_name else 65200.00
        return {
            "account_id": account_id,
            "current_balance": balance,
            "currency": "INR",
            "balance_type": "provider_reported",
            "balance_timestamp": datetime.now(timezone.utc).isoformat(),
            "sync_status": "synced"
        }

    def revoke_consent(self, consent_id: str) -> bool:
        logger.info(f"Sandbox AA consent {consent_id} marked REVOKED.")
        return True


class SetuAccountAggregatorAdapter(BaseBankAdapter):
    """
    Adapter for Setu Account Aggregator API (Bridge / FIU).
    Requires active Setu Client ID, Secret, and Product Instance ID.
    """
    def __init__(self, client_id: str, client_secret: str, product_instance_id: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.product_instance_id = product_instance_id
        self._validate_credentials()

    def _validate_credentials(self):
        if not self.client_id or not self.client_secret:
            raise BankProviderConfigurationError(
                "Setu Account Aggregator credentials are not configured. "
                "Please configure BANK_SETU_CLIENT_ID and BANK_SETU_CLIENT_SECRET in backend/.env "
                "following the instructions in docs/ACCOUNT_AGGREGATOR_EVALUATION.md."
            )

    def create_consent(self, user_id: str, phone_number: str, fip_ids: List[str], validity_days: int = 180) -> Dict[str, Any]:
        raise NotImplementedError("Live Setu AA requires active partner credentials. Use 'sandbox' mode for testing.")

    def get_consent_status(self, consent_handle: str) -> Dict[str, Any]:
        raise NotImplementedError("Live Setu AA requires active partner credentials.")

    def fetch_accounts(self, consent_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("Live Setu AA requires active partner credentials.")

    def sync_transactions(self, account_id: str, account_number_masked: str, institution_name: str, from_date: Optional[date] = None) -> Dict[str, Any]:
        raise NotImplementedError("Live Setu AA requires active partner credentials.")

    def get_balance(self, account_id: str, institution_name: str) -> Dict[str, Any]:
        raise NotImplementedError("Live Setu AA requires active partner credentials.")

    def revoke_consent(self, consent_id: str) -> bool:
        raise NotImplementedError("Live Setu AA requires active partner credentials.")


def get_bank_adapter() -> BaseBankAdapter:
    provider = getattr(settings, "BANK_PROVIDER", "sandbox").lower().strip()
    if provider == "setu":
        return SetuAccountAggregatorAdapter(
            client_id=getattr(settings, "BANK_SETU_CLIENT_ID", ""),
            client_secret=getattr(settings, "BANK_SETU_CLIENT_SECRET", ""),
            product_instance_id=getattr(settings, "BANK_SETU_PRODUCT_INSTANCE_ID", "")
        )
    return SandboxAccountAggregatorAdapter()
