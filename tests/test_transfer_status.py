from decimal import Decimal
from datetime import datetime, timezone

from src.api.schemas.transfer_schema import ErrorDetail, TransferStatusResponse


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
