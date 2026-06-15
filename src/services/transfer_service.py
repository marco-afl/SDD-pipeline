import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.api.schemas.transfer_schema import TransferRequest, TransferResponse, TransferStatusResponse
from src.repositories.account_repository import AccountRepository
from src.repositories.transfer_repository import TransferRepository
from src.services.audit_service import AuditService
from src.models.transfer import Transfer
from src.errors.transfer_errors import (
    InsufficientFundsError,
    OriginAccountNotFoundError,
    DestinationAccountNotFoundError,
    IdempotencyConflictError,
    TransferNotFoundError,
)


class TransferService:
    def __init__(self, db: Session):
        self.db = db
        self.account_repo = AccountRepository(db)
        self.transfer_repo = TransferRepository(db)
        self.audit_service = AuditService(db)

    def execute(self, req: TransferRequest, client_id: str, ip_address: str) -> TransferResponse:
        existing = self.transfer_repo.find_by_idempotency_key(req.idempotency_key)
        if existing:
            params_match = (
                existing.origin_account == req.origin_account
                and existing.destination_account == req.destination_account
                and Decimal(str(existing.amount)) == req.amount
                and existing.currency == req.currency
            )
            if params_match:
                return TransferResponse(
                    transfer_id=existing.transfer_id,
                    status=existing.status,
                    origin_account=existing.origin_account,
                    destination_account=existing.destination_account,
                    amount=Decimal(str(existing.amount)),
                    currency=existing.currency,
                    timestamp=existing.created_at,
                )
            raise IdempotencyConflictError()

        origin = self.account_repo.get_by_id_and_owner(req.origin_account, client_id)
        if not origin:
            raise OriginAccountNotFoundError()

        destination = self.account_repo.get_by_id(req.destination_account)
        if not destination:
            raise DestinationAccountNotFoundError()

        if Decimal(str(origin.balance)) < req.amount:
            raise InsufficientFundsError()

        now = datetime.now(timezone.utc)
        transfer_id = f"TRF-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        self.account_repo.debit(origin, req.amount)
        self.account_repo.credit(destination, req.amount)

        transfer = Transfer(
            transfer_id=transfer_id,
            idempotency_key=req.idempotency_key,
            origin_account=req.origin_account,
            destination_account=req.destination_account,
            amount=req.amount,
            currency=req.currency,
            description=req.description,
            status="completed",
            initiated_by=client_id,
            ip_address=ip_address,
            created_at=now,
        )
        self.transfer_repo.save(transfer)
        self.db.commit()

        self.audit_service.log_transfer(
            transfer_id=transfer_id,
            origin_account=req.origin_account,
            destination_account=req.destination_account,
            amount=req.amount,
            initiated_by=client_id,
            ip_address=ip_address,
        )

        return TransferResponse(
            transfer_id=transfer_id,
            status="completed",
            origin_account=req.origin_account,
            destination_account=req.destination_account,
            amount=req.amount,
            currency=req.currency,
            timestamp=now,
        )

    def get_status(self, transfer_id: str, client_id: str) -> TransferStatusResponse:
        transfer = self.transfer_repo.find_by_transfer_id(transfer_id)
        if transfer is None:
            raise TransferNotFoundError()
        return TransferStatusResponse(
            transfer_id=transfer.transfer_id,
            status=transfer.status,
            amount=Decimal(str(transfer.amount)),
            origin_account=transfer.origin_account,
            destination_account=transfer.destination_account,
            processed_at=transfer.created_at,
            error=None,
        )
