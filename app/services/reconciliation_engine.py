import re
from difflib import SequenceMatcher
from typing import List, Tuple, Optional
from app.schemas import BankTransaction, OpenInvoice, MatchDetail, MatchStatus, ReconciliationResponse

def normalize_text(text: str) -> str:
    """Removes special characters and lowercases text for matching."""
    if not text:
        return ""
    return re.sub(r'[^a-zA-Z0-9\s]', ' ', text).lower().strip()

def extract_invoice_numbers(title: str) -> List[str]:
    """
    Extracts potential invoice numbers using standard regex patterns:
    e.g. FV/2026/05/12, FS 123/2026, 2026/10/01, FV-10-2026
    """
    patterns = [
        r'\b(?:fv|fs|fa|faktura|inv)[\s\/\-\:]*([0-9a-zA-Z\/\-]+)\b',
        r'\b\d{1,5}\/\d{2,4}\/\d{2,4}\b',
        r'\b\d{1,5}\/[A-Z0-9]+\/\d{2,4}\b',
        r'\bFV[\s\-]*[0-9]+\b'
    ]
    results = []
    lower_title = title.lower()
    for p in patterns:
        matches = re.findall(p, lower_title)
        for m in matches:
            if isinstance(m, str) and len(m) >= 3:
                results.append(m.strip().replace(" ", ""))
    return results

def compute_similarity(a: str, b: str) -> float:
    """Computes string similarity ratio between 0.0 and 1.0."""
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()

def reconcile_bank_statement(
    transactions: List[BankTransaction],
    invoices: List[OpenInvoice]
) -> ReconciliationResponse:
    """
    3-Tier Reconciliation Engine:
    - Tier 1: Deterministic Exact Match (Invoice Number Regex + Exact Amount)
    - Tier 2: Heuristic Fuzzy Match (Counterparty Similarity + Amount Match)
    - Tier 3: Semantic Assistant (Confidence Scoring for Partial / Ambiguous Payments)
    """
    matches: List[MatchDetail] = []
    unsettled_invoices = {inv.invoice_id: inv for inv in invoices}
    
    for tx in transactions:
        tx_abs_amount = round(abs(tx.amount), 2)
        matched = False
        
        # --- TIER 1: EXACT MATCH ---
        extracted_nums = extract_invoice_numbers(tx.title)
        for inv_id, inv in list(unsettled_invoices.items()):
            clean_inv_num = inv.invoice_number.lower().replace(" ", "").replace("-", "").replace("/", "")
            
            # Check if invoice number matches pattern in title
            title_clean = tx.title.lower().replace(" ", "").replace("-", "").replace("/", "")
            if (clean_inv_num in title_clean or any(num in clean_inv_num for num in extracted_nums)) and \
               abs(inv.remaining_balance - tx_abs_amount) < 0.01:
                matches.append(MatchDetail(
                    transaction_id=tx.transaction_id,
                    invoice_id=inv.invoice_id,
                    invoice_number=inv.invoice_number,
                    amount=tx_abs_amount,
                    status=MatchStatus.EXACT_MATCH,
                    confidence_score=1.0,
                    audit_notes=f"Pełna zgodność: numer FV '{inv.invoice_number}' w tytule oraz idealna kwota {tx_abs_amount} PLN."
                ))
                del unsettled_invoices[inv_id]
                matched = True
                break
                
        if matched:
            continue

        # --- TIER 2: HEURISTIC / FUZZY MATCH ---
        best_candidate: Optional[Tuple[OpenInvoice, float]] = None
        for inv_id, inv in unsettled_invoices.items():
            name_sim = compute_similarity(tx.counterparty_name, inv.counterparty_name)
            amount_diff = abs(inv.remaining_balance - tx_abs_amount)
            
            if name_sim >= 0.70 and amount_diff < 0.01:
                if best_candidate is None or name_sim > best_candidate[1]:
                    best_candidate = (inv, name_sim)

        if best_candidate:
            inv, sim = best_candidate
            confidence = round(0.80 + (sim * 0.15), 2)
            matches.append(MatchDetail(
                transaction_id=tx.transaction_id,
                invoice_id=inv.invoice_id,
                invoice_number=inv.invoice_number,
                amount=tx_abs_amount,
                status=MatchStatus.FUZZY_SUGGESTION,
                confidence_score=confidence,
                audit_notes=f"Dopasowanie heurystyczne: Kontrahent '{tx.counterparty_name}' zbliżony do '{inv.counterparty_name}' (podobieństwo {int(sim*100)}%), zgodna kwota {tx_abs_amount} PLN."
            ))
            del unsettled_invoices[inv.invoice_id]
            continue

        # --- TIER 3: AI / SEMANTIC SUGGESTION (Partial / Contextual) ---
        semantic_candidate = None
        for inv_id, inv in unsettled_invoices.items():
            name_sim = compute_similarity(tx.counterparty_name, inv.counterparty_name)
            # Sprawdzenie wpłaty częściowej (np. zaliczka)
            if name_sim >= 0.60 and tx_abs_amount < inv.remaining_balance:
                semantic_candidate = (inv, name_sim)
                break
                
        if semantic_candidate:
            inv, sim = semantic_candidate
            matches.append(MatchDetail(
                transaction_id=tx.transaction_id,
                invoice_id=inv.invoice_id,
                invoice_number=inv.invoice_number,
                amount=tx_abs_amount,
                status=MatchStatus.AI_SEMANTIC_MATCH,
                confidence_score=0.75,
                audit_notes=f"Sugestia AI (Częściowa wpłata/Zaliczka): Kontrahent '{tx.counterparty_name}' wpłacił {tx_abs_amount} PLN na poczet FV '{inv.invoice_number}' (saldo pozostałe: {inv.remaining_balance} PLN). Wymaga akceptacji księgowego."
            ))
            continue

        # --- UNMATCHED ---
        matches.append(MatchDetail(
            transaction_id=tx.transaction_id,
            invoice_id=None,
            invoice_number=None,
            amount=tx_abs_amount,
            status=MatchStatus.UNMATCHED,
            confidence_score=0.0,
            audit_notes="Brak pasującej faktury lub kontrahenta w rejestrze rozrachunków. Wymagana weryfikacja ręczna."
        ))

    auto_matched = sum(1 for m in matches if m.status == MatchStatus.EXACT_MATCH)
    suggested = sum(1 for m in matches if m.status in [MatchStatus.FUZZY_SUGGESTION, MatchStatus.AI_SEMANTIC_MATCH])
    unmatched = sum(1 for m in matches if m.status == MatchStatus.UNMATCHED)

    return ReconciliationResponse(
        total_transactions=len(transactions),
        auto_matched=auto_matched,
        suggested=suggested,
        unmatched=unmatched,
        matches=matches
    )
