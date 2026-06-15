import pytest
from decimal import Decimal
from datetime import datetime, timezone

from src.api.schemas.transfer_schema import ErrorDetail, TransferStatusResponse
from src.services.transfer_service import TransferService
from src.errors.transfer_errors import TransferNotFoundError, TransferAccessDeniedError
from src.models.transfer import Transfer


# ---------------------------------------------------------------------------
# T01 — Schema unit tests
# ---------------------------------------------------------------------------

def test_transfer_status_response_minimal():
    resp = TransferStatusResponse(
        transfer_id="TRF-001",
        status="procesada",
        amount=Decimal("100.00"),
        origin_account="ACC-001",
        destination_account="ACC-002",
        processed_at=datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
    )
    assert resp.error is None


def test_transfer_status_response_with_error():
    resp = TransferStatusResponse(
        transfer_id="TRF-002",
        status="fallida",
        amount=Decimal("50.00"),
        origin_account="ACC-001",
        destination_account="ACC-002",
        processed_at=datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        error=ErrorDetail(code="TIMEOUT", message="La transferencia expiró."),
    )
    assert resp.error is not None
    assert resp.error.code == "TIMEOUT"
    assert resp.error.message == "La transferencia expiró."


def test_error_detail_fields():
    err = ErrorDetail(code="INSUFFICIENT_FUNDS", message="Saldo insuficiente.")
    assert err.code == "INSUFFICIENT_FUNDS"
    assert err.message == "Saldo insuficiente."


# ---------------------------------------------------------------------------
# T02 — Service-level query tests
# ---------------------------------------------------------------------------

def _seed_transfer(session, transfer_id="TRF-20260615-AABBCCDD", client_id="CLIENT-1"):
    t = Transfer(
        transfer_id=transfer_id,
        idempotency_key=f"idem-{transfer_id}",
        origin_account="ACC-001",
        destination_account="ACC-002",
        amount=Decimal("200.00"),
        currency="USD",
        status="completed",
        initiated_by=client_id,
        ip_address="127.0.0.1",
        created_at=datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
    )
    session.add(t)
    session.commit()
    return t


def test_get_status_returns_transfer_data(db_session):
    _seed_transfer(db_session)
    service = TransferService(db_session)
    result = service.get_status("TRF-20260615-AABBCCDD", "CLIENT-1")
    assert result.transfer_id == "TRF-20260615-AABBCCDD"
    assert result.status == "completed"
    assert result.amount == Decimal("200.00")
    assert result.origin_account == "ACC-001"
    assert result.destination_account == "ACC-002"
    assert result.error is None


def test_get_status_raises_not_found_for_unknown_id(db_session):
    service = TransferService(db_session)
    with pytest.raises(TransferNotFoundError):
        service.get_status("TRF-DOES-NOT-EXIST", "CLIENT-1")


# ---------------------------------------------------------------------------
# T03 — Ownership verification tests
# ---------------------------------------------------------------------------

def test_get_status_raises_access_denied_for_wrong_client(db_session):
    _seed_transfer(db_session, client_id="CLIENT-1")
    service = TransferService(db_session)
    with pytest.raises(TransferAccessDeniedError):
        service.get_status("TRF-20260615-AABBCCDD", "CLIENT-2")


def test_get_status_allows_owner_client(db_session):
    _seed_transfer(db_session, client_id="CLIENT-1")
    service = TransferService(db_session)
    result = service.get_status("TRF-20260615-AABBCCDD", "CLIENT-1")
    assert result.transfer_id == "TRF-20260615-AABBCCDD"


# ---------------------------------------------------------------------------
# T04 — Integration tests via TestClient
# ---------------------------------------------------------------------------

GET_URL = "/v1/transfers/{transfer_id}"
HEADERS = {"x-client-id": "CLIENT-1"}
CREATE_URL = "/v1/transfers"


def _create_transfer(client, transfer_id_hint="AABBCCDD"):
    import uuid
    payload = {
        "idempotency_key": str(uuid.uuid4()),
        "origin_account": "ACC-001",
        "destination_account": "ACC-002",
        "amount": "150.00",
        "currency": "USD",
    }
    resp = client.post(CREATE_URL, json=payload, headers=HEADERS)
    assert resp.status_code == 201
    return resp.json()["transfer_id"]


def test_get_transfer_status_happy_path(client):
    transfer_id = _create_transfer(client)
    resp = client.get(GET_URL.format(transfer_id=transfer_id), headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["transfer_id"] == transfer_id
    assert data["status"] == "completed"
    assert float(data["amount"]) == 150.0
    assert data["origin_account"] == "ACC-001"
    assert data["destination_account"] == "ACC-002"
    assert "processed_at" in data
    assert data["error"] is None


def test_get_transfer_status_not_found_returns_404(client):
    resp = client.get(GET_URL.format(transfer_id="TRF-DOES-NOT-EXIST"), headers=HEADERS)
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "TRANSFER_NOT_FOUND"


def test_get_transfer_status_wrong_client_returns_403(client):
    transfer_id = _create_transfer(client)
    resp = client.get(
        GET_URL.format(transfer_id=transfer_id),
        headers={"x-client-id": "CLIENT-2"},
    )
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "ACCESS_DENIED"


def test_get_transfer_status_all_fields_present(client):
    transfer_id = _create_transfer(client)
    resp = client.get(GET_URL.format(transfer_id=transfer_id), headers=HEADERS)
    data = resp.json()
    for field in ("transfer_id", "status", "amount", "origin_account", "destination_account", "processed_at"):
        assert field in data, f"Campo faltante: {field}"
