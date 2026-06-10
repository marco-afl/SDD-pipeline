from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.models.account import Account


class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id_and_owner(self, account_id: str, owner_id: str) -> Account | None:
        # with_for_update() is a no-op on SQLite; activates row locking on PostgreSQL
        return self.db.scalar(
            select(Account)
            .where(Account.account_id == account_id, Account.owner_id == owner_id)
            .with_for_update()
        )

    def get_by_id(self, account_id: str) -> Account | None:
        return self.db.scalar(
            select(Account).where(Account.account_id == account_id).with_for_update()
        )

    def debit(self, account: Account, amount: Decimal) -> None:
        account.balance = Decimal(str(account.balance)) - amount

    def credit(self, account: Account, amount: Decimal) -> None:
        account.balance = Decimal(str(account.balance)) + amount
