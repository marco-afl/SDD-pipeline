from sqlalchemy.orm import Session
from sqlalchemy import select
from src.models.transfer import Transfer


class TransferRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_idempotency_key(self, key: str) -> Transfer | None:
        return self.db.scalar(
            select(Transfer).where(Transfer.idempotency_key == key)
        )

    def save(self, transfer: Transfer) -> Transfer:
        self.db.add(transfer)
        self.db.flush()
        return transfer
