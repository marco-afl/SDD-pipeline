from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ErrorDetail(BaseModel):
    code: str
    message: str


class TransferStatusResponse(BaseModel):
    transfer_id: str
    status: str
    amount: Decimal
    origin_account: str
    destination_account: str
    processed_at: datetime
    error: Optional[ErrorDetail] = None

    model_config = {"from_attributes": True}


class TransferRequest(BaseModel):
    idempotency_key: str
    origin_account: str
    destination_account: str
    amount: Decimal
    currency: str = "USD"
    description: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("El monto debe ser mayor a cero.")
        if v.as_tuple().exponent < -2:
            raise ValueError("El monto no puede tener más de 2 decimales.")
        return v

    @model_validator(mode="after")
    def validate_different_accounts(self) -> "TransferRequest":
        if self.origin_account == self.destination_account:
            raise ValueError("La cuenta de origen y destino no pueden ser la misma.")
        return self


class TransferResponse(BaseModel):
    transfer_id: str
    status: str
    origin_account: str
    destination_account: str
    amount: Decimal
    currency: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    transfer_id: Optional[str] = None
    timestamp: datetime
