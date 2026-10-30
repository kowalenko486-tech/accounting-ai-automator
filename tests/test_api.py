from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "OPERATIONAL"

def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["healthy"] is True

def test_api_posting_endpoint():
    payload = {
        "invoice_number": "FV/2026/TEST/01",
        "issue_date": "2026-10-10",
        "due_date": "2026-10-24",
        "seller_name": "Test Seller Sp. z o.o.",
        "seller_nip": "5252344078",
        "buyer_name": "Test Buyer",
        "buyer_nip": "7791011327",
        "currency": "PLN",
        "items": [
            {
                "description": "Konsultacje IT",
                "cost_category": "USLUGI",
                "net_amount": 1000.0,
                "vat_rate": 0.23,
                "vat_amount": 230.0,
                "gross_amount": 1230.0
            }
        ]
    }
    response = client.post("/api/v1/invoices/validate-and-post", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_balanced"] is True
    assert data["total_gross"] == 1230.0
    assert len(data["postings"]) == 3
