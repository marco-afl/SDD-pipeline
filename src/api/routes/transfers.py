from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from src.database import get_db
from src.api.schemas.transfer_schema import TransferRequest, TransferResponse, ErrorResponse
from src.services.transfer_service import TransferService
from src.errors.transfer_errors import (
    InsufficientFundsError,
    OriginAccountNotFoundError,
    DestinationAccountNotFoundError,
    IdempotencyConflictError,
)

router = APIRouter()

_ERROR_MAP = {
    InsufficientFundsError: (
        422, "INSUFFICIENT_FUNDS",
        "El saldo disponible es insuficiente para completar la transferencia.",
    ),
    OriginAccountNotFoundError: (
        404, "ORIGIN_ACCOUNT_NOT_FOUND",
        "La cuenta de origen no fue encontrada.",
    ),
    DestinationAccountNotFoundError: (
        404, "DESTINATION_ACCOUNT_NOT_FOUND",
        "La cuenta de destino no fue encontrada.",
    ),
    IdempotencyConflictError: (
        409, "IDEMPOTENCY_CONFLICT",
        "La clave de idempotencia ya fue usada con parámetros distintos.",
    ),
}


@router.post("/v1/transfers", status_code=201, response_model=TransferResponse)
def create_transfer(
    request: Request,
    body: TransferRequest,
    db: Session = Depends(get_db),
    x_client_id: str = Header(...),
):
    ip_address = request.client.host if request.client else "unknown"
    service = TransferService(db)
    try:
        return service.execute(body, client_id=x_client_id, ip_address=ip_address)
    except (
        InsufficientFundsError,
        OriginAccountNotFoundError,
        DestinationAccountNotFoundError,
        IdempotencyConflictError,
    ) as exc:
        status_code, error_code, message = _ERROR_MAP[type(exc)]
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(
                error_code=error_code,
                message=message,
                transfer_id=None,
                timestamp=datetime.now(timezone.utc),
            ).model_dump(mode="json"),
        )
