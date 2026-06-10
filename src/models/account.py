from sqlalchemy import Column, String, Numeric
from src.database import Base


class Account(Base):
    __tablename__ = "accounts"

    account_id = Column(String, primary_key=True)
    owner_id = Column(String, nullable=False, index=True)
    balance = Column(Numeric(precision=12, scale=2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="USD")
