from sqlalchemy import Column, String, Numeric, DateTime
from datetime import datetime, timezone
from src.database import Base


class Transfer(Base):
    __tablename__ = "transfers"

    transfer_id = Column(String, primary_key=True)
    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    origin_account = Column(String, nullable=False)
    destination_account = Column(String, nullable=False)
    amount = Column(Numeric(precision=12, scale=2), nullable=False)
    currency = Column(String(3), nullable=False)
    description = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="completed")
    initiated_by = Column(String, nullable=False)
    ip_address = Column(String(45), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
