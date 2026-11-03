import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as instance:
        assert instance.get("/health").status_code == 200, "Train real artifacts before integration tests"
        yield instance


@pytest.fixture
def transaction():
    return {"Transaction_Date": "2024-02-01T14:30:00", "Transaction_Amount": 100.0, "Is_International": 0, "Account_Age_Days": 200, "Merchant_Category": "Travel", "Payment_Method": "UPI", "Device_Type": "Mobile", "Location": "Delhi"}
