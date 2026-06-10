from sqlalchemy import Column, String, Numeric, DateTime
from datetime import datetime, timezone
from src.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    event_id = Column(String, primary_key=True)
    transfer_id = Column(String, nullable=False, index=True)
    origin_account = Column(String, nullable=False)
    destination_account = Column(String, nullable=False)
    amount = Column(Numeric(precision=12, scale=2), nullable=False)
    initiated_by = Column(String, nullable=False)
    ip_address = Column(String(45), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
