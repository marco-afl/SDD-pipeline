import uuid

BASE_URL = "/v1/transfers"
HEADERS = {"x-client-id": "CLIENT-1"}


def _payload(**overrides):
    base = {
        "idempotency_key": str(uuid.uuid4()),
        "origin_account": "ACC-001",
        "destination_account": "ACC-002",
        "amount": "100.00",
        "currency": "USD",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_happy_path(client):
    resp = client.post(BASE_URL, json=_payload(), headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "completed"
    assert float(data["amount"]) == 100.0
    assert data["origin_account"] == "ACC-001"
    assert data["destination_account"] == "ACC-002"
    assert data["transfer_id"].startswith("TRF-")


# ---------------------------------------------------------------------------
# Idempotencia
# ---------------------------------------------------------------------------

def test_idempotency_same_key_same_params_returns_same_response(client):
    payload = _payload()
    first = client.post(BASE_URL, json=payload, headers=HEADERS)
    second = client.post(BASE_URL, json=payload, headers=HEADERS)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["transfer_id"] == second.json()["transfer_id"]


def test_idempotency_same_key_different_amount_returns_409(client):
    key = str(uuid.uuid4())
    client.post(BASE_URL, json=_payload(idempotency_key=key, amount="50.00"), headers=HEADERS)
    resp = client.post(BASE_URL, json=_payload(idempotency_key=key, amount="99.00"), headers=HEADERS)

    assert resp.status_code == 409
    assert resp.json()["error_code"] == "IDEMPOTENCY_CONFLICT"


# ---------------------------------------------------------------------------
# Errores de dominio
# ---------------------------------------------------------------------------

def test_insufficient_funds(client):
    resp = client.post(BASE_URL, json=_payload(amount="9999.00"), headers=HEADERS)
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "INSUFFICIENT_FUNDS"


def test_origin_account_not_found(client):
    resp = client.post(BASE_URL, json=_payload(origin_account="ACC-FAKE"), headers=HEADERS)
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "ORIGIN_ACCOUNT_NOT_FOUND"


def test_destination_account_not_found(client):
    resp = client.post(BASE_URL, json=_payload(destination_account="ACC-FAKE"), headers=HEADERS)
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "DESTINATION_ACCOUNT_NOT_FOUND"


# ---------------------------------------------------------------------------
# Errores de validación
# ---------------------------------------------------------------------------

def test_negative_amount(client):
    resp = client.post(BASE_URL, json=_payload(amount="-10.00"), headers=HEADERS)
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "INVALID_AMOUNT"


def test_zero_amount(client):
    resp = client.post(BASE_URL, json=_payload(amount="0.00"), headers=HEADERS)
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "INVALID_AMOUNT"


def test_amount_with_more_than_two_decimals(client):
    resp = client.post(BASE_URL, json=_payload(amount="10.999"), headers=HEADERS)
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "INVALID_AMOUNT"


def test_same_origin_and_destination_account(client):
    resp = client.post(BASE_URL, json=_payload(destination_account="ACC-001"), headers=HEADERS)
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "SAME_ACCOUNT_TRANSFER"
