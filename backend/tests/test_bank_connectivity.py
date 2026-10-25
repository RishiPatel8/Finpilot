import pytest
from datetime import date, timedelta
from app.models.bank import BankConsent, BankAccount, BankSyncLog
from app.models.financial import Transaction


def test_bank_consent_lifecycle_and_account_discovery(client):
    # 1. Register test user
    reg = client.post("/api/v1/auth/register", json={
        "email": "bank_user1@example.com",
        "password": "Password123!",
        "full_name": "Bank User One",
        "role": "salaried"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Initiate consent
    init_res = client.post("/api/v1/bank/consent/initiate", json={
        "phone_number": "9876543210",
        "fip_ids": ["FIP_HDFC", "FIP_ICICI"],
        "validity_days": 180
    }, headers=headers)
    assert init_res.status_code == 200
    consent_data = init_res.json()
    assert consent_data["status"] == "PENDING"
    assert "cnh_sandbox" in consent_data["consent_handle"]
    consent_id = consent_data["id"]

    # 3. Check consent status
    status_res = client.get(f"/api/v1/bank/consent/{consent_id}", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "PENDING"

    # 4. Approve consent (Simulated AA Grant)
    approve_res = client.post(f"/api/v1/bank/consent/{consent_id}/approve", headers=headers)
    assert approve_res.status_code == 200
    accounts = approve_res.json()
    assert len(accounts) == 2
    assert any("HDFC" in a["institution_name"] for a in accounts)
    assert any("ICICI" in a["institution_name"] for a in accounts)

    # 5. Verify linked accounts endpoint
    accs_res = client.get("/api/v1/bank/accounts", headers=headers)
    assert accs_res.status_code == 200
    assert len(accs_res.json()) == 2

    # 6. Verify initial synced transactions created in database
    tx_res = client.get("/api/v1/transactions", headers=headers)
    assert tx_res.status_code == 200
    txns = tx_res.json()
    assert len(txns) > 0
    assert any(t.get("source") == "bank_sync" for t in txns)

    # 7. Revoke consent
    revoke_res = client.post(f"/api/v1/bank/consent/{consent_id}/revoke", headers=headers)
    assert revoke_res.status_code == 200
    assert "revoked" in revoke_res.json()["message"].lower()

    # Verify accounts marked stale
    accs_stale = client.get("/api/v1/bank/accounts", headers=headers).json()
    assert all(a["sync_status"] == "stale" for a in accs_stale)


def test_bank_transaction_idempotent_sync_and_duplicate_prevention(client):
    reg = client.post("/api/v1/auth/register", json={
        "email": "bank_user2@example.com",
        "password": "Password123!",
        "full_name": "Bank User Two",
        "role": "salaried"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Initiate & approve
    init_res = client.post("/api/v1/bank/consent/initiate", json={
        "phone_number": "9812345678",
        "validity_days": 90
    }, headers=headers)
    consent_id = init_res.json()["id"]
    client.post(f"/api/v1/bank/consent/{consent_id}/approve", headers=headers)

    accounts = client.get("/api/v1/bank/accounts", headers=headers).json()
    account_id = accounts[0]["id"]

    initial_txns = client.get("/api/v1/transactions", headers=headers).json()
    initial_count = len(initial_txns)
    assert initial_count > 0

    # Trigger manual sync again on the same account
    sync_res = client.post(f"/api/v1/bank/accounts/{account_id}/sync", headers=headers)
    assert sync_res.status_code == 200
    assert sync_res.json()["synced_count"] == 0  # 0 duplicates imported

    # Verify total transactions did not increase
    after_sync_txns = client.get("/api/v1/transactions", headers=headers).json()
    assert len(after_sync_txns) == initial_count


def test_bank_cross_user_isolation(client):
    # User A
    reg_a = client.post("/api/v1/auth/register", json={
        "email": "user_alpha@example.com",
        "password": "Password123!",
        "full_name": "User Alpha",
        "role": "salaried"
    })
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User B
    reg_b = client.post("/api/v1/auth/register", json={
        "email": "user_beta@example.com",
        "password": "Password123!",
        "full_name": "User Beta",
        "role": "freelancer"
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A connects bank
    init_a = client.post("/api/v1/bank/consent/initiate", json={"phone_number": "9111111111"}, headers=headers_a)
    consent_id_a = init_a.json()["id"]
    client.post(f"/api/v1/bank/consent/{consent_id_a}/approve", headers=headers_a)
    accs_a = client.get("/api/v1/bank/accounts", headers=headers_a).json()
    acc_id_a = accs_a[0]["id"]

    # User B cannot access User A's consent
    forbidden_consent = client.get(f"/api/v1/bank/consent/{consent_id_a}", headers=headers_b)
    assert forbidden_consent.status_code == 404

    # User B cannot sync User A's bank account
    forbidden_sync = client.post(f"/api/v1/bank/accounts/{acc_id_a}/sync", headers=headers_b)
    assert forbidden_sync.status_code == 404

    # User B has zero bank accounts
    accs_b = client.get("/api/v1/bank/accounts", headers=headers_b).json()
    assert len(accs_b) == 0


def test_bank_consent_callback_success(client):
    reg = client.post("/api/v1/auth/register", json={
        "email": "callback_success@example.com",
        "password": "Password123!",
        "full_name": "Callback Success User",
        "role": "salaried"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Initiate consent
    init_res = client.post("/api/v1/bank/consent/initiate", json={
        "phone_number": "9876543210",
        "validity_days": 180
    }, headers=headers)
    assert init_res.status_code == 200
    consent_data = init_res.json()
    handle = consent_data["consent_handle"]
    assert "/bank/consent/callback" in consent_data["redirect_url"]

    # 2. Simulate return from AA redirect with query params
    cb_res = client.post("/api/v1/bank/consent/callback", json={
        "consent_handle": handle,
        "status": "ACCEPT"
    }, headers=headers)
    assert cb_res.status_code == 200
    cb_data = cb_res.json()
    assert cb_data["status"] == "ACTIVE"
    assert cb_data["accounts_linked"] == 2
    assert len(cb_data["accounts"]) == 2

    # 3. Verify accounts list endpoint reflects newly synced accounts
    accs = client.get("/api/v1/bank/accounts", headers=headers).json()
    assert len(accs) == 2


def test_bank_consent_callback_user_rejection(client):
    reg = client.post("/api/v1/auth/register", json={
        "email": "callback_reject@example.com",
        "password": "Password123!",
        "full_name": "Callback Reject User",
        "role": "salaried"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    init_res = client.post("/api/v1/bank/consent/initiate", json={
        "phone_number": "9876543210"
    }, headers=headers)
    handle = init_res.json()["consent_handle"]

    # Simulate user clicked "Decline" on AA portal
    cb_res = client.post("/api/v1/bank/consent/callback", json={
        "consent_handle": handle,
        "status": "REJECT",
        "error": "USER_DECLINED"
    }, headers=headers)
    assert cb_res.status_code == 200
    cb_data = cb_res.json()
    assert cb_data["status"] == "REJECTED"
    assert cb_data["accounts_linked"] == 0

    # Ensure no bank accounts were created
    accs = client.get("/api/v1/bank/accounts", headers=headers).json()
    assert len(accs) == 0


def test_bank_consent_callback_anti_spoofing_security(client, monkeypatch):
    """
    Ensures that if query parameter reports status=ACCEPT, but provider adapter reports
    REJECTED or PENDING, FinPilot DOES NOT trust the query parameter and refuses to link accounts.
    """
    reg = client.post("/api/v1/auth/register", json={
        "email": "callback_spoof@example.com",
        "password": "Password123!",
        "full_name": "Callback Spoof User",
        "role": "salaried"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    init_res = client.post("/api/v1/bank/consent/initiate", json={
        "phone_number": "9876543210"
    }, headers=headers)
    consent_id = init_res.json()["id"]

    # Mock the adapter to simulate that AA portal status is REJECTED
    from app.bank.adapter import get_bank_adapter
    adapter = get_bank_adapter()
    monkeypatch.setattr(adapter, "get_consent_status", lambda h: {
        "consent_handle": h,
        "status": "REJECTED",
        "error": "OTP_EXPIRED"
    })
    monkeypatch.setattr("app.api.v1.endpoints.bank.get_bank_adapter", lambda: adapter)

    # Spoofed request claims status=ACCEPT in request body/query param
    spoofed_res = client.post("/api/v1/bank/consent/callback", json={
        "consent_handle": init_res.json()["consent_handle"],
        "status": "ACCEPT"
    }, headers=headers)
    assert spoofed_res.status_code == 200
    res_data = spoofed_res.json()
    assert res_data["status"] == "REJECTED"
    assert res_data["accounts_linked"] == 0

    # Verify accounts remain zero
    accs = client.get("/api/v1/bank/accounts", headers=headers).json()
    assert len(accs) == 0


def test_finvu_adapter_configuration_and_factory(monkeypatch):
    from app.bank.adapter import (
        FinvuAccountAggregatorAdapter,
        BankProviderConfigurationError,
        get_bank_adapter,
    )
    from app.core.config import settings

    # Missing credentials must raise BankProviderConfigurationError
    with pytest.raises(BankProviderConfigurationError):
        FinvuAccountAggregatorAdapter(client_id="", client_secret="")

    # Valid initialization
    finvu = FinvuAccountAggregatorAdapter(
        client_id="finvu_test_client",
        client_secret="finvu_test_secret",
        redirect_url="https://confidingly-ketonic-evelina.ngrok-free.dev/bank/consent/callback"
    )
    assert finvu.client_id == "finvu_test_client"
    assert finvu.redirect_url == "https://confidingly-ketonic-evelina.ngrok-free.dev/bank/consent/callback"

    # Test factory returns Finvu adapter when BANK_PROVIDER=finvu
    monkeypatch.setattr(settings, "BANK_PROVIDER", "finvu")
    monkeypatch.setattr(settings, "BANK_FINVU_CLIENT_ID", "finvu_client_id")
    monkeypatch.setattr(settings, "BANK_FINVU_CLIENT_SECRET", "finvu_client_sec")
    adapter = get_bank_adapter()
    assert isinstance(adapter, FinvuAccountAggregatorAdapter)


def test_finvu_missing_credentials_fails_clearly_without_fallback(client, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "BANK_PROVIDER", "finvu")
    monkeypatch.setattr(settings, "BANK_FINVU_CLIENT_ID", "")
    monkeypatch.setattr(settings, "BANK_FINVU_CLIENT_SECRET", "")

    reg = client.post("/api/v1/auth/register", json={
        "email": "finvu_nocreds@example.com",
        "password": "Password123!",
        "full_name": "No Creds User",
        "role": "salaried"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/api/v1/bank/consent/initiate", json={"phone_number": "9876543210"}, headers=headers)
    # Must fail with 503 Service Unavailable and clear message; NOT fall back to sandbox
    assert res.status_code == 503
    assert "Finvu Account Aggregator credentials are not configured" in res.json()["detail"]


def test_finvu_consent_initiation_with_mocked_http_and_ngrok_callback(client, monkeypatch):
    import httpx
    from app.core.config import settings

    monkeypatch.setattr(settings, "BANK_PROVIDER", "finvu")
    monkeypatch.setattr(settings, "BANK_FINVU_CLIENT_ID", "finvu_uat_client_id")
    monkeypatch.setattr(settings, "BANK_FINVU_CLIENT_SECRET", "finvu_uat_client_secret")
    monkeypatch.setattr(settings, "BANK_REDIRECT_URL", "https://confidingly-ketonic-evelina.ngrok-free.dev/bank/consent/callback")

    reg = client.post("/api/v1/auth/register", json={
        "email": "finvu_user@example.com",
        "password": "Password123!",
        "full_name": "Finvu Test User",
        "role": "salaried"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    captured_requests = []
    orig_post = httpx.Client.post

    def mock_post(self, url, *args, **kwargs):
        url_str = str(url)
        if "testserver" in url_str or not url_str.startswith("http"):
            return orig_post(self, url, *args, **kwargs)
        captured_requests.append({
            "url": url_str,
            "json": kwargs.get("json"),
            "headers": kwargs.get("headers")
        })
        return httpx.Response(
            status_code=200,
            json={
                "ver": "2.0.0",
                "timestamp": "2026-10-23T18:00:00Z",
                "txnid": "tx_mock_123",
                "ConsentHandle": "cnh_finvu_live_handle_998877",
                "status": "PENDING",
                "url": "https://web-uat.finvu.in/?consentHandle=cnh_finvu_live_handle_998877&redirectUrl=https://confidingly-ketonic-evelina.ngrok-free.dev/bank/consent/callback"
            },
            request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    init_res = client.post("/api/v1/bank/consent/initiate", json={
        "phone_number": "+919876543210",
        "validity_days": 180
    }, headers=headers)

    assert init_res.status_code == 200
    res_data = init_res.json()
    assert res_data["provider"] == "finvu"
    assert res_data["consent_handle"] == "cnh_finvu_live_handle_998877"
    assert "https://web-uat.finvu.in" in res_data["redirect_url"]
    assert "confidingly-ketonic-evelina.ngrok-free.dev" in res_data["redirect_url"]

    # Verify Finvu contract details sent in POST request
    assert len(captured_requests) == 1
    req_sent = captured_requests[0]
    assert "/Consent" in req_sent["url"]
    assert req_sent["headers"]["x-client-id"] == "finvu_uat_client_id"
    assert req_sent["headers"]["x-client-secret"] == "finvu_uat_client_secret"
    assert req_sent["json"]["ConsentDetail"]["Customer"]["id"] == "9876543210@finvu"
    assert req_sent["json"]["redirectUrl"] == "https://confidingly-ketonic-evelina.ngrok-free.dev/bank/consent/callback"


def test_finvu_authoritative_status_verification_and_no_unauthorized_sbi(client, monkeypatch):
    import httpx
    from app.core.config import settings

    monkeypatch.setattr(settings, "BANK_PROVIDER", "finvu")
    monkeypatch.setattr(settings, "BANK_FINVU_CLIENT_ID", "finvu_uat_client_id")
    monkeypatch.setattr(settings, "BANK_FINVU_CLIENT_SECRET", "finvu_uat_client_secret")

    reg = client.post("/api/v1/auth/register", json={
        "email": "finvu_sbi_check@example.com",
        "password": "Password123!",
        "full_name": "Finvu SBI Guard User",
        "role": "salaried"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    orig_post = httpx.Client.post
    orig_get = httpx.Client.get

    def mock_post(self, url, *args, **kwargs):
        url_str = str(url)
        if "testserver" in url_str or not url_str.startswith("http"):
            return orig_post(self, url, *args, **kwargs)
        return httpx.Response(
            status_code=200,
            json={
                "ConsentHandle": "cnh_finvu_auth_test_1122",
                "url": "https://web-uat.finvu.in/?consentHandle=cnh_finvu_auth_test_1122"
            },
            request=httpx.Request("POST", url)
        )

    def mock_get(self, url, *args, **kwargs):
        url_str = str(url)
        if "testserver" in url_str or not url_str.startswith("http"):
            return orig_get(self, url, *args, **kwargs)
        if "/Consent/handle/" in url_str:
            return httpx.Response(
                status_code=200,
                json={
                    "ConsentStatus": {
                        "id": "cst_finvu_verified_1122",
                        "status": "ACTIVE"
                    }
                },
                request=httpx.Request("GET", url)
            )
        elif "/accounts" in url_str:
            return httpx.Response(
                status_code=200,
                json={
                    "accounts": [
                        {
                            "institution_name": "HDFC Bank",
                            "account_number_masked": "XXXX-XXXX-9911",
                            "account_type": "savings",
                            "ifsc_code": "HDFC0000001",
                            "currency": "INR",
                            "current_balance": 92000.00
                        },
                        {
                            "institution_name": "Axis Bank",
                            "account_number_masked": "XXXX-XXXX-3344",
                            "account_type": "current",
                            "ifsc_code": "UTIB0000001",
                            "currency": "INR",
                            "current_balance": 45000.00
                        }
                    ]
                },
                request=httpx.Request("GET", url)
            )
        elif "/FI/fetch" in url_str:
            return httpx.Response(status_code=200, json={"transactions": []}, request=httpx.Request("GET", url))
        elif "/FI/balance" in url_str:
            return httpx.Response(status_code=200, json={"current_balance": 92000.0}, request=httpx.Request("GET", url))
        return httpx.Response(status_code=404, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.Client, "post", mock_post)
    monkeypatch.setattr(httpx.Client, "get", mock_get)

    # 1. Initiate consent
    init_res = client.post("/api/v1/bank/consent/initiate", json={"phone_number": "9876543210"}, headers=headers)
    assert init_res.status_code == 200

    # 2. Return from redirect
    cb_res = client.post("/api/v1/bank/consent/callback", json={
        "consent_handle": "cnh_finvu_auth_test_1122",
        "status": "ACCEPT"
    }, headers=headers)
    assert cb_res.status_code == 200
    cb_data = cb_res.json()
    assert cb_data["status"] == "ACTIVE"
    assert cb_data["accounts_linked"] == 2

    # 3. Verify that SBI is NOT linked since provider didn't return it
    linked_accounts = cb_data["accounts"]
    institutions = [a["institution_name"] for a in linked_accounts]
    assert "HDFC Bank" in institutions
    assert "Axis Bank" in institutions
    assert not any("SBI" in inst or "State Bank of India" in inst for inst in institutions)


def test_provider_selection_hierarchy(monkeypatch):
    from app.bank.adapter import (
        FinvuAccountAggregatorAdapter,
        SetuAccountAggregatorAdapter,
        SandboxAccountAggregatorAdapter,
        get_bank_adapter
    )
    from app.core.config import settings

    # 1. Finvu
    monkeypatch.setattr(settings, "BANK_PROVIDER", "finvu")
    monkeypatch.setattr(settings, "BANK_FINVU_CLIENT_ID", "id")
    monkeypatch.setattr(settings, "BANK_FINVU_CLIENT_SECRET", "sec")
    assert isinstance(get_bank_adapter(), FinvuAccountAggregatorAdapter)

    # 2. Setu
    monkeypatch.setattr(settings, "BANK_PROVIDER", "setu")
    monkeypatch.setattr(settings, "BANK_SETU_CLIENT_ID", "id")
    monkeypatch.setattr(settings, "BANK_SETU_CLIENT_SECRET", "sec")
    monkeypatch.setattr(settings, "BANK_SETU_PRODUCT_INSTANCE_ID", "inst")
    assert isinstance(get_bank_adapter(), SetuAccountAggregatorAdapter)

    # 3. Sandbox
    monkeypatch.setattr(settings, "BANK_PROVIDER", "sandbox")
    assert isinstance(get_bank_adapter(), SandboxAccountAggregatorAdapter)


def _make_jws(raw_bytes: bytes, secret: str = "whsec_test_secret_12345") -> str:
    import base64
    import hmac
    import hashlib
    import json
    hdr = json.dumps({"alg": "HS256", "typ": "JWT"}).encode("utf-8")
    b64_hdr = base64.urlsafe_b64encode(hdr).decode("ascii").rstrip("=")
    b64_payload = base64.urlsafe_b64encode(raw_bytes).decode("ascii").rstrip("=")
    signing_input = f"{b64_hdr}.{b64_payload}".encode("ascii")
    sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    b64_sig = base64.urlsafe_b64encode(sig).decode("ascii").rstrip("=")
    return f"{b64_hdr}..{b64_sig}"


def test_rebit_webhook_invalid_signature(client, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "BANK_WEBHOOK_SECRET", "whsec_test_secret_12345")

    # Request with missing signature headers
    res = client.post("/api/v1/bank/Consent/Notification", json={
        "ver": "2.0.0",
        "timestamp": "2026-10-23T18:00:00Z",
        "txnid": "txn_invalid_sig_001",
        "Notifier": {"type": "AA", "id": "finvu-aa"},
        "ConsentStatusNotification": {
            "consentHandle": "cnh_any",
            "consentStatus": "ACTIVE"
        }
    })
    assert res.status_code == 401
    assert "signature" in res.json()["detail"].lower()


def test_rebit_webhook_malformed_payload(client, monkeypatch):
    from app.core.config import settings
    secret = "whsec_test_secret_12345"
    monkeypatch.setattr(settings, "BANK_WEBHOOK_SECRET", secret)

    malformed_body = b'{"ver": "2.0.0", "missing_required_txnid": true}'
    jws = _make_jws(malformed_body, secret)

    res = client.post(
        "/api/v1/bank/Consent/Notification",
        content=malformed_body,
        headers={"x-jws-signature": jws, "Content-Type": "application/json"}
    )
    assert res.status_code == 400
    assert "malformed" in res.json()["detail"].lower()


def test_rebit_webhook_unknown_consent_handle(client, monkeypatch):
    import json
    from app.core.config import settings
    secret = "whsec_test_secret_12345"
    monkeypatch.setattr(settings, "BANK_WEBHOOK_SECRET", secret)

    payload = {
        "ver": "2.0.0",
        "timestamp": "2026-10-23T18:00:00Z",
        "txnid": "txn_unknown_handle_999",
        "Notifier": {"type": "AA", "id": "finvu-aa"},
        "ConsentStatusNotification": {
            "consentHandle": "cnh_nonexistent_handle_12345",
            "consentStatus": "ACTIVE"
        }
    }
    raw_body = json.dumps(payload).encode("utf-8")
    jws = _make_jws(raw_body, secret)

    res = client.post(
        "/api/v1/bank/Consent/Notification",
        content=raw_body,
        headers={"x-jws-signature": jws, "Content-Type": "application/json"}
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_rebit_webhook_consent_active_and_idempotency(client, monkeypatch):
    import json
    from app.core.config import settings
    secret = "whsec_test_secret_12345"
    monkeypatch.setattr(settings, "BANK_WEBHOOK_SECRET", secret)

    # 1. Register user & initiate consent
    reg = client.post("/api/v1/auth/register", json={
        "email": "webhook_active@example.com",
        "password": "Password123!",
        "full_name": "Webhook Active User",
        "role": "salaried"
    })
    token = reg.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {token}"}

    init_res = client.post("/api/v1/bank/consent/initiate", json={
        "phone_number": "9876543210"
    }, headers=user_headers)
    handle = init_res.json()["consent_handle"]

    # 2. Account Aggregator delivers server-to-server ConsentStatusNotification
    payload = {
        "ver": "2.0.0",
        "timestamp": "2026-10-23T18:00:00Z",
        "txnid": "txn_rebit_active_001",
        "Notifier": {"type": "AA", "id": "finvu-aa"},
        "ConsentStatusNotification": {
            "consentId": f"cst_{handle[-10:]}",
            "consentHandle": handle,
            "consentStatus": "ACTIVE"
        }
    }
    raw_body = json.dumps(payload).encode("utf-8")
    jws = _make_jws(raw_body, secret)

    webhook_res = client.post(
        "/api/v1/bank/Consent/Notification",
        content=raw_body,
        headers={"x-jws-signature": jws, "Content-Type": "application/json"}
    )
    assert webhook_res.status_code == 200
    res_data = webhook_res.json()
    assert res_data["response"] == "OK"
    assert res_data["txnid"] == "txn_rebit_active_001"

    # Verify accounts were linked in user account
    accs = client.get("/api/v1/bank/accounts", headers=user_headers).json()
    assert len(accs) == 2

    # 3. Idempotency test: duplicate delivery with same txnid must return OK without duplicate errors
    dup_res = client.post(
        "/api/v1/bank/Consent/Notification",
        content=raw_body,
        headers={"x-jws-signature": jws, "Content-Type": "application/json"}
    )
    assert dup_res.status_code == 200
    assert dup_res.json()["response"] == "OK"

    # Accounts count remains unchanged
    accs_after_dup = client.get("/api/v1/bank/accounts", headers=user_headers).json()
    assert len(accs_after_dup) == 2


def test_rebit_webhook_consent_revocation(client, monkeypatch):
    import json
    from app.core.config import settings
    secret = "whsec_test_secret_12345"
    monkeypatch.setattr(settings, "BANK_WEBHOOK_SECRET", secret)

    reg = client.post("/api/v1/auth/register", json={
        "email": "webhook_revoke@example.com",
        "password": "Password123!",
        "full_name": "Webhook Revoke User",
        "role": "salaried"
    })
    token = reg.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {token}"}

    init_res = client.post("/api/v1/bank/consent/initiate", json={
        "phone_number": "9876543210"
    }, headers=user_headers)
    consent_id = init_res.json()["id"]
    handle = init_res.json()["consent_handle"]

    # Approve first
    client.post(f"/api/v1/bank/consent/{consent_id}/approve", headers=user_headers)
    accs_initial = client.get("/api/v1/bank/accounts", headers=user_headers).json()
    assert all(a["sync_status"] == "synced" for a in accs_initial)

    # Deliver REVOKED notification via unified /webhook endpoint
    payload = {
        "ver": "2.0.0",
        "timestamp": "2026-10-23T18:05:00Z",
        "txnid": "txn_revoke_notif_001",
        "Notifier": {"type": "AA", "id": "finvu-aa"},
        "ConsentStatusNotification": {
            "consentHandle": handle,
            "consentStatus": "REVOKED"
        }
    }
    raw_body = json.dumps(payload).encode("utf-8")
    jws = _make_jws(raw_body, secret)

    res = client.post(
        "/api/v1/bank/webhook",
        content=raw_body,
        headers={"x-jws-signature": jws, "Content-Type": "application/json"}
    )
    assert res.status_code == 200
    assert res.json()["response"] == "OK"

    # Verify accounts are now marked stale
    accs_stale = client.get("/api/v1/bank/accounts", headers=user_headers).json()
    assert all(a["sync_status"] == "stale" for a in accs_stale)


def test_rebit_webhook_anti_spoofing(client, monkeypatch):
    """
    Ensures that if webhook claims consentStatus=ACTIVE, but provider adapter reports
    REJECTED or FAILED, FinPilot refuses to activate the consent or link accounts.
    """
    import json
    from app.core.config import settings
    secret = "whsec_test_secret_12345"
    monkeypatch.setattr(settings, "BANK_WEBHOOK_SECRET", secret)

    reg = client.post("/api/v1/auth/register", json={
        "email": "webhook_spoof@example.com",
        "password": "Password123!",
        "full_name": "Webhook Spoof User",
        "role": "salaried"
    })
    token = reg.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {token}"}

    init_res = client.post("/api/v1/bank/consent/initiate", json={
        "phone_number": "9876543210"
    }, headers=user_headers)
    handle = init_res.json()["consent_handle"]

    # Mock the adapter to simulate that AA portal status is REJECTED
    from app.bank.adapter import get_bank_adapter
    adapter = get_bank_adapter()
    monkeypatch.setattr(adapter, "get_consent_status", lambda h: {
        "consent_handle": h,
        "status": "REJECTED",
        "error": "OTP_FAILED"
    })
    monkeypatch.setattr("app.api.v1.endpoints.bank.get_bank_adapter", lambda: adapter)

    payload = {
        "ver": "2.0.0",
        "timestamp": "2026-10-23T18:10:00Z",
        "txnid": "txn_spoofed_active_001",
        "Notifier": {"type": "AA", "id": "finvu-aa"},
        "ConsentStatusNotification": {
            "consentHandle": handle,
            "consentStatus": "ACTIVE"
        }
    }
    raw_body = json.dumps(payload).encode("utf-8")
    jws = _make_jws(raw_body, secret)

    res = client.post(
        "/api/v1/bank/Consent/Notification",
        content=raw_body,
        headers={"x-jws-signature": jws, "Content-Type": "application/json"}
    )
    assert res.status_code == 200
    assert res.json()["response"] == "OK"

    # Check consent status in DB is not ACTIVE and no accounts exist
    accs = client.get("/api/v1/bank/accounts", headers=user_headers).json()
    assert len(accs) == 0


def test_rebit_webhook_fi_notification(client, monkeypatch):
    import json
    from app.core.config import settings
    secret = "whsec_test_secret_12345"
    monkeypatch.setattr(settings, "BANK_WEBHOOK_SECRET", secret)

    payload = {
        "ver": "2.0.0",
        "timestamp": "2026-10-23T18:15:00Z",
        "txnid": "txn_fi_ready_001",
        "Notifier": {"type": "AA", "id": "finvu-aa"},
        "FIStatusNotification": {
            "sessionId": "session_uuid_12345",
            "sessionStatus": "COMPLETED",
            "FIStatusResponse": [
                {
                    "fipId": "FIP_HDFC",
                    "accounts": [
                        {"linkRefNumber": "ACC_HDFC_4921", "FIStatus": "READY"}
                    ]
                }
            ]
        }
    }
    raw_body = json.dumps(payload).encode("utf-8")
    jws = _make_jws(raw_body, secret)

    res = client.post(
        "/api/v1/bank/FI/Notification",
        content=raw_body,
        headers={"x-jws-signature": jws, "Content-Type": "application/json"}
    )
    assert res.status_code == 200
    assert res.json()["response"] == "OK"
    assert res.json()["txnid"] == "txn_fi_ready_001"
