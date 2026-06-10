import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.database import get_db, Base
from src.models.account import Account


@pytest.fixture(scope="function")
def client(tmp_path):
    url = f"sqlite:///{tmp_path}/test.db"
    test_engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    with TestSession() as session:
        session.add_all([
            Account(account_id="ACC-001", owner_id="CLIENT-1", balance=Decimal("5000.00"), currency="USD"),
            Account(account_id="ACC-002", owner_id="CLIENT-2", balance=Decimal("1000.00"), currency="USD"),
            Account(account_id="ACC-003", owner_id="CLIENT-3", balance=Decimal("0.00"), currency="USD"),
        ])
        session.commit()

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
