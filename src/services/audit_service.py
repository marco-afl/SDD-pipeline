import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log_transfer(
        self,
        transfer_id: str,
        origin_account: str,
        destination_account: str,
        amount: Decimal,
        initiated_by: str,
        ip_address: str,
    ) -> None:
        log = AuditLog(
            event_id=str(uuid.uuid4()),
            transfer_id=transfer_id,
            origin_account=origin_account,
            destination_account=destination_account,
            amount=amount,
            initiated_by=initiated_by,
            ip_address=ip_address,
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(log)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            # Audit failure is non-blocking; transfer already committed
