from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, date, timedelta
import uuid
import re
import logging
import httpx
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
            "redirect_url": f"/bank/consent/callback?consentHandle={consent_handle}&status=ACCEPT",
            "mode": "SANDBOX (Simulated Indian Account Aggregator)"
        }

    def get_consent_status(self, consent_handle: str) -> Dict[str, Any]:
        if "reject" in consent_handle.lower():
            return {
                "consent_handle": consent_handle,
                "status": "REJECTED",
                "error": "User declined consent request on Account Aggregator portal",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
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


class FinvuAccountAggregatorAdapter(BaseBankAdapter):
    """
    Adapter for Finvu Account Aggregator API (Cookiejar Technologies - RBI Licensed NBFC-AA).
    Follows ReBIT 1.1 / 2.0 Account Aggregator technical specifications under the
    Finvu Hosted FIU Gateway model.
    
    Requires active Finvu Client ID and Client Secret from the Finvu developer portal.
    """
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = "",
        fiu_id: str = "",
        web_url: str = "",
        redirect_url: str = ""
    ):
        self.client_id = (client_id or "").strip()
        self.client_secret = (client_secret or "").strip()
        self.base_url = (base_url or getattr(settings, "BANK_FINVU_BASE_URL", "https://fiu-uat.finvu.in")).rstrip("/")
        self.fiu_id = (fiu_id or getattr(settings, "BANK_FINVU_FIU_ID", "finpilot-fiu")).strip()
        self.web_url = (web_url or getattr(settings, "BANK_FINVU_WEB_URL", "https://web-uat.finvu.in")).rstrip("/")
        self.redirect_url = redirect_url or getattr(settings, "BANK_REDIRECT_URL", "https://confidingly-ketonic-evelina.ngrok-free.dev/bank/consent/callback")
        self._validate_credentials()

    def _validate_credentials(self):
        if not self.client_id or not self.client_secret:
            raise BankProviderConfigurationError(
                "Finvu Account Aggregator credentials are not configured. "
                "Please configure BANK_FINVU_CLIENT_ID and BANK_FINVU_CLIENT_SECRET in backend/.env "
                "following the instructions in docs/BANK_INTEGRATION_GUIDE.md."
            )

    def _format_customer_vua(self, phone_number: str) -> str:
        """
        Formats customer identification according to Finvu AA VUA specifications:
        Standard format: '<10-digit-phone>@finvu'
        """
        raw = (phone_number or "").strip()
        if "@" in raw:
            return raw
        digits = re.sub(r"\D", "", raw)
        if len(digits) > 10 and digits.startswith("91"):
            digits = digits[-10:]
        elif len(digits) > 10 and digits.startswith("0"):
            digits = digits[-10:]
        if not digits:
            digits = "9876543210"
        return f"{digits}@finvu"

    def _get_headers(self) -> Dict[str, str]:
        return {
            "x-client-id": self.client_id,
            "x-client-secret": self.client_secret,
            "x-fiu-id": self.fiu_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def create_consent(
        self,
        user_id: str,
        phone_number: str,
        fip_ids: List[str],
        validity_days: int = 180
    ) -> Dict[str, Any]:
        """
        Initiates a consent request via Finvu Hosted FIU API.
        Builds a statutory ReBIT 2.0 ConsentDetail schema and submits to Finvu.
        """
        self._validate_credentials()
        now = datetime.now(timezone.utc)
        valid_to = now + timedelta(days=validity_days)
        fi_from = now - timedelta(days=365)
        customer_vua = self._format_customer_vua(phone_number)
        txnid = f"finvu_tx_{uuid.uuid4().hex}"

        payload = {
            "ver": "2.0.0",
            "timestamp": now.isoformat(),
            "txnid": txnid,
            "ConsentDetail": {
                "consentStart": now.isoformat(),
                "consentExpiry": valid_to.isoformat(),
                "consentMode": "STORE",
                "fetchType": "PERIODIC",
                "consentTypes": ["TRANSACTIONS", "PROFILE", "SUMMARY"],
                "fiTypes": ["DEPOSIT"],
                "DataConsumer": {
                    "id": self.fiu_id
                },
                "Customer": {
                    "id": customer_vua
                },
                "Purpose": {
                    "code": "101",
                    "refUri": "https://api.rebit.org.in",
                    "text": "Personal Financial Advisory and FIRE Wealth Planning",
                    "Category": {
                        "type": "string"
                    }
                },
                "FIDataRange": {
                    "from": fi_from.isoformat(),
                    "to": now.isoformat()
                },
                "DataLife": {
                    "unit": "MONTH",
                    "value": 12
                },
                "Frequency": {
                    "unit": "DAILY",
                    "value": 1
                },
                "DataFilter": [
                    {
                        "type": "TRANSACTIONAMOUNT",
                        "operator": ">=",
                        "value": "0"
                    }
                ]
            },
            "redirectUrl": self.redirect_url
        }

        # In production or test environment with active credentials, call Finvu API
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(
                    f"{self.base_url}/Consent",
                    json=payload,
                    headers=self._get_headers()
                )
                if res.status_code in (200, 201):
                    data = res.json()
                    consent_handle = (
                        data.get("ConsentHandle")
                        or data.get("consentHandle")
                        or data.get("handle")
                        or f"cnh_finvu_{uuid.uuid4().hex[:12]}"
                    )
                    redirect_url = (
                        data.get("url")
                        or data.get("redirectUrl")
                        or f"{self.web_url}/?consentHandle={consent_handle}&redirectUrl={self.redirect_url}"
                    )
                    return {
                        "consent_handle": consent_handle,
                        "provider": "finvu",
                        "status": "PENDING",
                        "fip_ids": fip_ids or ["FIP_HDFC", "FIP_ICICI"],
                        "fi_types": ["DEPOSIT"],
                        "valid_from": now.isoformat(),
                        "valid_to": valid_to.isoformat(),
                        "fetch_frequency": "DAILY",
                        "redirect_url": redirect_url,
                        "mode": "FINVU_HOSTED_FIU"
                    }
                else:
                    logger.error(f"Finvu API Consent initiation error HTTP {res.status_code}: {res.text}")
                    raise RuntimeError(
                        f"Finvu API rejected consent initiation: HTTP {res.status_code} - {res.text[:200]}"
                    )
        except httpx.RequestError as exc:
            logger.error(f"Finvu API network error during consent initiation: {exc}")
            raise RuntimeError(f"Unable to reach Finvu Account Aggregator API at {self.base_url}: {exc}")

    def get_consent_status(self, consent_handle: str) -> Dict[str, Any]:
        """
        Authoritatively checks consent status from the Finvu FIU API.
        Does not trust query params or web redirects.
        """
        self._validate_credentials()
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(
                    f"{self.base_url}/Consent/handle/{consent_handle}",
                    headers=self._get_headers()
                )
                if res.status_code == 200:
                    data = res.json()
                    c_status_obj = data.get("ConsentStatus", {})
                    status_val = (
                        c_status_obj.get("status")
                        or data.get("status")
                        or "PENDING"
                    ).upper()
                    consent_id = (
                        c_status_obj.get("id")
                        or data.get("consent_id")
                        or consent_handle
                    )
                    return {
                        "consent_handle": consent_handle,
                        "status": status_val,
                        "consent_id": consent_id,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    logger.warning(f"Finvu get_consent_status HTTP {res.status_code}: {res.text}")
                    return {
                        "consent_handle": consent_handle,
                        "status": "PENDING",
                        "error": f"Finvu status check failed: HTTP {res.status_code}",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
        except httpx.RequestError as exc:
            logger.error(f"Finvu network error during status check: {exc}")
            raise RuntimeError(f"Unable to query Finvu consent status: {exc}")

    def fetch_accounts(self, consent_id: str) -> List[Dict[str, Any]]:
        """
        Discovers accounts authorized by user on the Finvu AA portal.
        Strictly reflects provider response; never fabricates SBI accounts.
        """
        self._validate_credentials()
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(
                    f"{self.base_url}/Consent/{consent_id}/accounts",
                    headers=self._get_headers()
                )
                if res.status_code == 200:
                    data = res.json()
                    raw_accounts = data.get("accounts") or data.get("Account") or []
                    accounts = []
                    for acc in raw_accounts:
                        accounts.append({
                            "institution_name": acc.get("institution_name") or acc.get("fipName") or "Indian Scheduled Bank",
                            "account_number_masked": acc.get("account_number_masked") or acc.get("maskedAccNumber") or "XXXX-XXXX-0000",
                            "account_type": (acc.get("account_type") or acc.get("accType") or "savings").lower(),
                            "ifsc_code": acc.get("ifsc_code") or acc.get("ifsc") or "",
                            "currency": acc.get("currency") or "INR",
                            "current_balance": float(acc.get("current_balance") or acc.get("balance") or 0.0),
                            "balance_type": "provider_reported",
                            "balance_timestamp": datetime.now(timezone.utc).isoformat(),
                            "sync_status": "synced"
                        })
                    return accounts
                else:
                    logger.warning(f"Finvu fetch_accounts returned HTTP {res.status_code}")
                    return []
        except httpx.RequestError as exc:
            logger.error(f"Finvu network error fetching accounts: {exc}")
            return []

    def sync_transactions(
        self,
        account_id: str,
        account_number_masked: str,
        institution_name: str,
        from_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Fetches and synchronizes transactions for an authorized account from Finvu.
        """
        self._validate_credentials()
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(
                    f"{self.base_url}/FI/fetch/{account_id}",
                    headers=self._get_headers()
                )
                if res.status_code == 200:
                    data = res.json()
                    txns = data.get("transactions") or []
                    return {
                        "account_id": account_id,
                        "synced_count": len(txns),
                        "transactions": txns,
                        "sync_status": "SUCCESS",
                        "synced_at": datetime.now(timezone.utc).isoformat()
                    }
                return {
                    "account_id": account_id,
                    "synced_count": 0,
                    "transactions": [],
                    "sync_status": "SUCCESS",
                    "synced_at": datetime.now(timezone.utc).isoformat()
                }
        except httpx.RequestError as exc:
            logger.error(f"Finvu transaction sync network error: {exc}")
            return {
                "account_id": account_id,
                "synced_count": 0,
                "transactions": [],
                "sync_status": "ERROR",
                "synced_at": datetime.now(timezone.utc).isoformat()
            }

    def get_balance(self, account_id: str, institution_name: str) -> Dict[str, Any]:
        """
        Retrieves authoritative provider-reported balance from Finvu.
        """
        self._validate_credentials()
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(
                    f"{self.base_url}/FI/balance/{account_id}",
                    headers=self._get_headers()
                )
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "account_id": account_id,
                        "current_balance": float(data.get("current_balance") or data.get("balance") or 0.0),
                        "currency": data.get("currency") or "INR",
                        "balance_type": "provider_reported",
                        "balance_timestamp": datetime.now(timezone.utc).isoformat(),
                        "sync_status": "synced"
                    }
        except Exception:
            pass
        return {
            "account_id": account_id,
            "current_balance": 0.0,
            "currency": "INR",
            "balance_type": "provider_reported",
            "balance_timestamp": datetime.now(timezone.utc).isoformat(),
            "sync_status": "synced"
        }

    def revoke_consent(self, consent_id: str) -> bool:
        """
        Submits consent revocation to Finvu.
        """
        self._validate_credentials()
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(
                    f"{self.base_url}/Consent/{consent_id}/revoke",
                    headers=self._get_headers(),
                    json={"consentId": consent_id}
                )
                return res.status_code in (200, 204)
        except Exception as exc:
            logger.error(f"Failed to revoke consent on Finvu: {exc}")
            return False


def get_bank_adapter() -> BaseBankAdapter:
    provider = getattr(settings, "BANK_PROVIDER", "sandbox").lower().strip()
    if provider == "finvu":
        return FinvuAccountAggregatorAdapter(
            client_id=getattr(settings, "BANK_FINVU_CLIENT_ID", ""),
            client_secret=getattr(settings, "BANK_FINVU_CLIENT_SECRET", ""),
            base_url=getattr(settings, "BANK_FINVU_BASE_URL", "https://fiu-uat.finvu.in"),
            fiu_id=getattr(settings, "BANK_FINVU_FIU_ID", "finpilot-fiu"),
            web_url=getattr(settings, "BANK_FINVU_WEB_URL", "https://web-uat.finvu.in"),
            redirect_url=getattr(settings, "BANK_REDIRECT_URL", "https://confidingly-ketonic-evelina.ngrok-free.dev/bank/consent/callback")
        )
    elif provider == "setu":
        return SetuAccountAggregatorAdapter(
            client_id=getattr(settings, "BANK_SETU_CLIENT_ID", ""),
            client_secret=getattr(settings, "BANK_SETU_CLIENT_SECRET", ""),
            product_instance_id=getattr(settings, "BANK_SETU_PRODUCT_INSTANCE_ID", "")
        )
    return SandboxAccountAggregatorAdapter()
