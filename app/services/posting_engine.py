from typing import List
from app.schemas import InvoiceInput, PostingResponse, AccountPosting, EntrySide

COST_ACCOUNT_MAP = {
    "USLUGI": ("401-01", "Koszty usług obcych"),
    "MATERIALY": ("402-01", "Koszty zużycia materiałów i energii"),
    "MEDIA": ("402-02", "Koszty energii i mediów"),
    "DEFAULT": ("409-99", "Pozostałe koszty rodzajowe")
}

def generate_invoice_postings(invoice: InvoiceInput) -> PostingResponse:
    """
    Generates balanced double-entry accounting records (Wn / Ma)
    for a validated purchase invoice.
    """
    postings: List[AccountPosting] = []
    total_net = sum(item.net_amount for item in invoice.items)
    total_vat = sum(item.vat_amount for item in invoice.items)
    total_gross = sum(item.gross_amount for item in invoice.items)

    # 1. Pozycje kosztowe (Wn - Winien)
    for idx, item in enumerate(invoice.items, 1):
        acct_num, acct_name = COST_ACCOUNT_MAP.get(
            item.cost_category.upper(),
            COST_ACCOUNT_MAP["DEFAULT"]
        )
        postings.append(AccountPosting(
            account_number=acct_num,
            account_name=acct_name,
            side=EntrySide.WN,
            amount=round(item.net_amount, 2),
            currency=invoice.currency,
            description=f"FV {invoice.invoice_number} poz. {idx}: {item.description}"
        ))

    # 2. Pozycja VAT naliczony (Wn - Winien)
    if total_vat > 0:
        postings.append(AccountPosting(
            account_number="221-01",
            account_name="VAT naliczony i jego rozliczenie (23%)",
            side=EntrySide.WN,
            amount=round(total_vat, 2),
            currency=invoice.currency,
            description=f"VAT z faktury {invoice.invoice_number}"
        ))

    # 3. Zobowiązanie wobec dostawcy (Ma - Ma)
    clean_nip = invoice.seller_nip.replace("-", "").strip()
    postings.append(AccountPosting(
        account_number=f"201-2-{clean_nip}",
        account_name=f"Rozrachunki z dostawcami: {invoice.seller_name[:30]}",
        side=EntrySide.MA,
        amount=round(total_gross, 2),
        currency=invoice.currency,
        description=f"Zobowiązanie z FV {invoice.invoice_number} ({invoice.seller_name})"
    ))

    # Weryfikacja bilansu (Zasada podwójnego zapisu: Suma Wn == Suma Ma)
    wn_sum = round(sum(p.amount for p in postings if p.side == EntrySide.WN), 2)
    ma_sum = round(sum(p.amount for p in postings if p.side == EntrySide.MA), 2)
    is_balanced = abs(wn_sum - ma_sum) < 0.01

    return PostingResponse(
        invoice_number=invoice.invoice_number,
        seller_name=invoice.seller_name,
        total_net=round(total_net, 2),
        total_vat=round(total_vat, 2),
        total_gross=round(total_gross, 2),
        postings=postings,
        is_balanced=is_balanced,
        status="POSTED_SUCCESSFULLY" if is_balanced else "POSTING_IMBALANCE_ERROR"
    )
