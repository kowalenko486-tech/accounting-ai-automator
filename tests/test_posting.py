from datetime import date
import pytest
from pydantic import ValidationError
from app.schemas import InvoiceInput, InvoiceItem, EntrySide
from app.services.posting_engine import generate_invoice_postings
from app.validators import validate_nip_modulo11, validate_iban_mod97

# Prawidłowe NIPy ze zweryfikowaną sumą kontrolną
VALID_SELLER_NIP = "5252344078"
VALID_BUYER_NIP = "7791011327"
INVALID_NIP = "1234567890"

def test_nip_validator():
    assert validate_nip_modulo11(VALID_SELLER_NIP) is True
    assert validate_nip_modulo11(VALID_BUYER_NIP) is True
    assert validate_nip_modulo11(INVALID_NIP) is False
    assert validate_nip_modulo11("abc") is False

def test_iban_validator():
    # Prawidłowy polski IBAN
    valid_iban = "PL61109010140000071219812874"
    assert validate_iban_mod97(valid_iban) is True
    assert validate_iban_mod97("PL00000000000000000000000000") is False

def test_successful_invoice_posting():
    invoice = InvoiceInput(
        invoice_number="FV/2026/10/45",
        issue_date=date(2026, 10, 15),
        due_date=date(2026, 10, 29),
        seller_name="Chmura & Serwery Sp. z o.o.",
        seller_nip=VALID_SELLER_NIP,
        buyer_name="Biuro Rachunkowe Nowa Era",
        buyer_nip=VALID_BUYER_NIP,
        currency="PLN",
        items=[
            InvoiceItem(
                description="Usługi hostingowe i serwer dedykowany",
                cost_category="USLUGI",
                net_amount=1000.0,
                vat_rate=0.23,
                vat_amount=230.0,
                gross_amount=1230.0
            ),
            InvoiceItem(
                description="Materiały biurowe i papier",
                cost_category="MATERIALY",
                net_amount=200.0,
                vat_rate=0.23,
                vat_amount=46.0,
                gross_amount=246.0
            )
        ]
    )

    result = generate_invoice_postings(invoice)

    assert result.is_balanced is True
    assert result.total_net == 1200.0
    assert result.total_vat == 276.0
    assert result.total_gross == 1476.0

    wn_entries = [p for p in result.postings if p.side == EntrySide.WN]
    ma_entries = [p for p in result.postings if p.side == EntrySide.MA]

    total_wn = sum(p.amount for p in wn_entries)
    total_ma = sum(p.amount for p in ma_entries)
    assert total_wn == 1476.0
    assert total_ma == 1476.0

def test_invalid_nip_raises_validation_error():
    with pytest.raises(ValidationError):
        InvoiceInput(
            invoice_number="FV/2026/01",
            issue_date=date(2026, 10, 1),
            due_date=date(2026, 10, 15),
            seller_name="Test",
            seller_nip=INVALID_NIP,
            buyer_name="Kupiec",
            buyer_nip=VALID_BUYER_NIP,
            items=[]
        )

def test_invalid_item_arithmetic_raises_validation_error():
    with pytest.raises(ValidationError):
        InvoiceItem(
            description="Błędne wyliczenie",
            cost_category="USLUGI",
            net_amount=100.0,
            vat_rate=0.23,
            vat_amount=50.0,  # Błędny VAT! Powinno być 23.0
            gross_amount=150.0
        )
