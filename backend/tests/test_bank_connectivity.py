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
