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
