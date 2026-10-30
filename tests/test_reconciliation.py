from datetime import date
from app.schemas import BankTransaction, OpenInvoice, MatchStatus
from app.services.reconciliation_engine import reconcile_bank_statement

def test_three_tier_reconciliation():
    transactions = [
        # Tier 1: Exact match with invoice number in title
        BankTransaction(
            transaction_id="tx_01",
            booking_date=date(2026, 10, 20),
            amount=-1230.00,
            counterparty_name="AWS Cloud Services",
            title="Zapłata za fakturę FV/2026/10/45 - usługi IT"
        ),
        # Tier 2: Fuzzy match - typo in company name, no invoice number in title
        BankTransaction(
            transaction_id="tx_02",
            booking_date=date(2026, 10, 21),
            amount=-500.00,
            counterparty_name="Polski Prad i Gaz Spolka Akcyjna",
            title="Przelew za energię elektryczną"
        ),
        # Tier 3: Partial payment (Zaliczka)
        BankTransaction(
            transaction_id="tx_03",
            booking_date=date(2026, 10, 22),
            amount=-1000.00,
            counterparty_name="Kancelaria Prawna Nova",
            title="Zaliczka na poczet obsługi prawnej"
        ),
        # Unmatched
        BankTransaction(
            transaction_id="tx_04",
            booking_date=date(2026, 10, 23),
            amount=-99.99,
            counterparty_name="Nieznany Podmiot XYZ",
            title="Opłata manipulacyjna"
        )
    ]

    open_invoices = [
        OpenInvoice(
            invoice_id="inv_01",
            invoice_number="FV/2026/10/45",
            counterparty_name="AWS Cloud Services",
            counterparty_nip="5252344078",
            gross_amount=1230.00,
            remaining_balance=1230.00
        ),
        OpenInvoice(
            invoice_id="inv_02",
            invoice_number="FV/2026/09/88",
            counterparty_name="Polski Prąd i Gaz S.A.",
            counterparty_nip="7791011327",
            gross_amount=500.00,
            remaining_balance=500.00
        ),
        OpenInvoice(
            invoice_id="inv_03",
            invoice_number="FV/2026/10/01",
            counterparty_name="Kancelaria Prawna Nova sp. k.",
            counterparty_nip="5252344078",
            gross_amount=3000.00,
            remaining_balance=3000.00
        )
    ]

    response = reconcile_bank_statement(transactions, open_invoices)

    assert response.total_transactions == 4
    assert response.auto_matched == 1
    assert response.suggested == 2
    assert response.unmatched == 1

    # Check Tier 1
    m1 = response.matches[0]
    assert m1.transaction_id == "tx_01"
    assert m1.status == MatchStatus.EXACT_MATCH
    assert m1.confidence_score == 1.0
    assert m1.invoice_number == "FV/2026/10/45"

    # Check Tier 2
    m2 = response.matches[1]
    assert m2.transaction_id == "tx_02"
    assert m2.status == MatchStatus.FUZZY_SUGGESTION
    assert m2.confidence_score >= 0.85
    assert m2.invoice_number == "FV/2026/09/88"

    # Check Tier 3
    m3 = response.matches[2]
    assert m3.transaction_id == "tx_03"
    assert m3.status == MatchStatus.AI_SEMANTIC_MATCH
    assert m3.invoice_number == "FV/2026/10/01"

    # Check Unmatched
    m4 = response.matches[3]
    assert m4.transaction_id == "tx_04"
    assert m4.status == MatchStatus.UNMATCHED
