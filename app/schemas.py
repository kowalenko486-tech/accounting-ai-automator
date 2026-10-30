from enum import Enum
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field, field_validator, model_validator
from app.validators import validate_nip_modulo11, validate_iban_mod97

class EntrySide(str, Enum):
    WN = "WN"  # Debit (Winien)
    MA = "MA"  # Credit (Ma)

class MatchStatus(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    FUZZY_SUGGESTION = "FUZZY_SUGGESTION"
    AI_SEMANTIC_MATCH = "AI_SEMANTIC_MATCH"
    UNMATCHED = "UNMATCHED"

class InvoiceItem(BaseModel):
    description: str
    cost_category: str = Field(default="USLUGI", description="Kategoria kosztowa (np. USLUGI, MATERIALY, MEDIA)")
    net_amount: float = Field(gt=0, description="Kwota netto")
    vat_rate: float = Field(ge=0, le=1.0, description="Stawka VAT (np. 0.23)")
    vat_amount: float = Field(ge=0, description="Kwota VAT")
    gross_amount: float = Field(gt=0, description="Kwota brutto")

    @model_validator(mode="after")
    def verify_item_math(self):
        expected_vat = round(self.net_amount * self.vat_rate, 2)
        if abs(expected_vat - self.vat_amount) > 0.05:
            raise ValueError(f"Nieprawidłowa kwota VAT: {self.vat_amount} (oczekiwano: {expected_vat})")
        expected_gross = round(self.net_amount + self.vat_amount, 2)
        if abs(expected_gross - self.gross_amount) > 0.05:
            raise ValueError(f"Nieprawidłowa kwota brutto: {self.gross_amount} (oczekiwano: {expected_gross})")
        return self

class InvoiceInput(BaseModel):
    invoice_number: str
    issue_date: date
    due_date: date
    seller_name: str
    seller_nip: str
    buyer_name: str
    buyer_nip: str
    currency: str = "PLN"
    items: List[InvoiceItem]

    @field_validator("seller_nip", "buyer_nip")
    @classmethod
    def check_nip(cls, v: str) -> str:
        if not validate_nip_modulo11(v):
            raise ValueError(f"Niepoprawny NIP (błąd sumy kontrolnej modulo-11): {v}")
        return v

class AccountPosting(BaseModel):
    account_number: str
    account_name: str
    side: EntrySide
    amount: float
    currency: str = "PLN"
    description: str

class PostingResponse(BaseModel):
    invoice_number: str
    seller_name: str
    total_net: float
    total_vat: float
    total_gross: float
    postings: List[AccountPosting]
    is_balanced: bool = True
    status: str = "POSTED_SUCCESSFULLY"

class BankTransaction(BaseModel):
    transaction_id: str
    booking_date: date
    amount: float = Field(description="Ujemna dla wydatków, dodatnia dla wpływów")
    currency: str = "PLN"
    counterparty_name: str
    counterparty_iban: Optional[str] = None
    title: str

class OpenInvoice(BaseModel):
    invoice_id: str
    invoice_number: str
    counterparty_name: str
    counterparty_nip: str
    gross_amount: float
    remaining_balance: float
    currency: str = "PLN"

class MatchDetail(BaseModel):
    transaction_id: str
    invoice_id: Optional[str] = None
    invoice_number: Optional[str] = None
    amount: float
    status: MatchStatus
    confidence_score: float = Field(ge=0.0, le=1.0)
    audit_notes: str

class ReconciliationResponse(BaseModel):
    total_transactions: int
    auto_matched: int
    suggested: int
    unmatched: int
    matches: List[MatchDetail]
