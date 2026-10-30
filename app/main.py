from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel
from app.schemas import InvoiceInput, PostingResponse, BankTransaction, OpenInvoice, ReconciliationResponse
from app.services.posting_engine import generate_invoice_postings
from app.services.reconciliation_engine import reconcile_bank_statement

app = FastAPI(
    title="Accounting AI Automator & Reconciliation Engine",
    description="Silnik automatycznego księgowania faktur na kontach, 3-stopniowego uzgadniania wyciągów bankowych i deterministycznej walidacji Pydantic.",
    version="1.0.0"
)

class ReconcileRequest(BaseModel):
    transactions: List[BankTransaction]
    open_invoices: List[OpenInvoice]

@app.get("/")
def read_root():
    return {
        "service": "Accounting AI Automator",
        "version": "1.0.0",
        "status": "OPERATIONAL",
        "docs_url": "/docs",
        "author": "Andrzej Kowalczyk"
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "healthy": True}

@app.post("/api/v1/invoices/validate-and-post", response_model=PostingResponse)
def post_invoice(invoice: InvoiceInput):
    """
    Przyjmuje dane faktury, weryfikuje sumy kontrolne NIP (modulo-11)
    oraz arytmetykę netto/VAT/brutto, po czym generuje zbilansowane dekrety księgowe Wn/Ma.
    """
    try:
        posting_result = generate_invoice_postings(invoice)
        if not posting_result.is_balanced:
            raise HTTPException(status_code=422, detail="Naruszenie zasady podwójnego zapisu: Bilans Wn/Ma niezgodny.")
        return posting_result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/bank/reconcile", response_model=ReconciliationResponse)
def reconcile_statement(req: ReconcileRequest):
    """
    Wykonuje 3-poziomowe uzgodnienie transakcji bankowych z rejestrem niezapłaconych faktur:
    1. Poziom Twardy: regex numeru faktury w tytule + dokładna kwota (100% pewności).
    2. Poziom Heurystyczny: dopasowanie kontrahenta + zgodność kwoty.
    3. Poziom Asystenta AI: wykrywanie zaliczek i wpłat częściowych z obliczeniem Confidence Score.
    """
    return reconcile_bank_statement(req.transactions, req.open_invoices)
