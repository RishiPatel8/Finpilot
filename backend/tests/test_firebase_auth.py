import pytest


def test_firebase_new_user_registration_flow(client):
    # Sign up via mock Firebase Google token
    mock_token = "mock-firebase:google_uid_999:kavita@example.com:Kavita Krishnan"
    res = client.post("/api/v1/auth/firebase-login", json={"id_token": mock_token, "role": "freelancer"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "kavita@example.com"
    assert data["user"]["firebase_uid"] == "google_uid_999"
    assert data["user"]["auth_provider"] == "firebase_google"

    # Returning user sign in with same Firebase UID
    res_returning = client.post("/api/v1/auth/firebase-login", json={"id_token": mock_token})
    assert res_returning.status_code == 200
    assert res_returning.json()["user"]["id"] == data["user"]["id"]


def test_firebase_explicit_account_linking_protection(client):
    # 1. User registers locally with email and password
    local_reg = client.post("/api/v1/auth/register", json={
        "email": "vikram@example.com",
        "full_name": "Vikram Singh",
        "password": "LocalPassword123!",
        "role": "salaried"
    })
    assert local_reg.status_code == 201

    # 2. Someone tries to login with Google token for vikram@example.com WITHOUT password
    # Must be REJECTED with 409 Conflict to prevent unauthorized account takeover!
    mock_token = "mock-firebase:google_uid_vikram:vikram@example.com:Vikram Singh"
    res_unlinked = client.post("/api/v1/auth/firebase-login", json={"id_token": mock_token})
    assert res_unlinked.status_code == 409
    assert "Please provide your existing password" in res_unlinked.json()["detail"]

    # 3. User provides WRONG password
    res_wrong_pw = client.post("/api/v1/auth/firebase-login", json={
        "id_token": mock_token,
        "link_password": "WrongPassword!"
    })
    assert res_wrong_pw.status_code == 401

    # 4. User provides CORRECT password -> Account is explicitly linked!
    res_linked = client.post("/api/v1/auth/firebase-login", json={
        "id_token": mock_token,
        "link_password": "LocalPassword123!"
    })
    assert res_linked.status_code == 200
    linked_data = res_linked.json()
    assert linked_data["user"]["auth_provider"] == "linked"
    assert linked_data["user"]["firebase_uid"] == "google_uid_vikram"


def test_firebase_invalid_token_rejected(client):
    res = client.post("/api/v1/auth/firebase-login", json={"id_token": ""})
    assert res.status_code == 401
