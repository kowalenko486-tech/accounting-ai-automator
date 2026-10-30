# Accounting AI Automator 💼⚡
### AI & Rules-Based Accounting Engine | Automatic Invoice Posting, 3-Tier Bank Reconciliation & Pydantic Zero-Hallucination Gate

[![CI Tests](https://github.com/kowalenko486-tech/accounting-ai-automator/actions/workflows/ci.yml/badge.svg)](https://github.com/kowalenko486-tech/accounting-ai-automator/actions)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?style=flat&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Production_Ready-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2_Gate-E92063?style=flat&logo=pydantic)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Accounting AI Automator** to nowoczesny mikroserwis w **Pythonie (FastAPI)** zaprojektowany z myślą o wyzwaniach nowoczesnych biur rachunkowych. Łączy moc modeli AI z deterministycznymi regułami księgowymi, automatyzując dwa najbardziej czasochłonne procesy w księgowości:
1. **Automatyczne dekretowanie i księgowanie faktur na kontach zespołu 2 i 4** (zgodnie z zasadą podwójnego zapisu Wn/Ma).
2. **3-stopniowe inteligentne dopasowywanie transakcji bankowych do faktur i rozrachunków** (Tier 1: Deterministyczny Regex $\rightarrow$ Tier 2: Heurystyka Levenshteina $\rightarrow$ Tier 3: Asystent AI z oceną wiarygodności).

---

## 🛡️ Architektura Zero-Hallucination Gate

W finansach i księgowości modele AI **nigdy nie mogą mieć bezpośredniego prawa zapisu do księgi głównej**. Każdy odczyt z OCR/LLM przechodzi przez rygorystyczną bramkę walidacyjną:

```text
  [ Faktura / Wyciąg Bankowy ] 
               │
               ▼
   [ Warstwa AI / OCR / LLM ]
 (Ekstrakcja danych i intencji)
               │
               ▼
   [ Pydantic Gate & Validators ]
   ├── Weryfikacja NIP (modulo-11)
   ├── Weryfikacja IBAN (ISO mod-97)
   └── Walidacja sum arytmetycznych: Netto + VAT = Brutto
               │
               ▼
   [ Deterministyczny Silnik Księgowy ]
   ├── Generowanie dekretów Wn / Ma (Zasada podwójnego zapisu)
   └── 3-poziomowy silnik uzgadniania wyciągów (Reconciliation)
               │
               ▼
  [ API / Eksport do ERP (Optima, Symfonia, Enova) ]
```

---

## ✨ Główne Moduły

### 1. Automatyczne Księgowanie Faktur (`/api/v1/invoices/validate-and-post`)
* Weryfikuje poprawność formalną i arytmetyczną faktury.
* Mapuje kategorie kosztowe na konta zespołu 4 (np. `401-01` Usługi obce, `402-01` Materiały i energia, `402-02` Media).
* Automatycznie nalicza VAT na koncie `221-01` oraz tworzy rozrachunek z dostawcą na koncie `201-2-{NIP}` po stronie Ma.
* Sprawdza bilansowanie się dekretu: $\sum Wn == \sum Ma$ przed zatwierdzeniem.

### 2. Trójstopniowe Uzgadnianie Wyciągów Bankowych (`/api/v1/bank/reconcile`)
* **Tier 1 (Deterministyczny / Regex):** Wyszukuje numer faktury w tytule przelewu oraz sprawdza zgodność co do grosza. Pewność: `1.0 (100%)`.
* **Tier 2 (Heurystyczny / Fuzzy Matching):** Gdy w tytule przelewu brakuje numeru faktury, silnik oblicza podobieństwo nazwy kontrahenta (analiza fonetyczna / Levenshtein) i paruje ze zgodną kwotą. Pewność: `> 0.85`.
* **Tier 3 (Asystent AI / Wpłaty częściowe):** Wykrywa zaliczki, wpłaty częściowe i transakcje o nietypowych opisach, generując propozycję rozliczenia wraz z notatką audytową dla księgowego.

---

## 🚀 Szybki Start

### 1. Klonowanie repozytorium
```bash
git clone https://github.com/kowalenko486-tech/accounting-ai-automator.git
cd accounting-ai-automator
```

### 2. Instalacja zależności
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Uruchomienie mikroserwisu
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Dokumentacja Swagger UI dostępna pod adresem: `http://localhost:8000/docs`.

---

## 🧪 Testy Jednostkowe & Integracyjne

Repozytorium posiada 100% pokrycia kluczowych ścieżek biznesowych (algorytmy modulo, reguły dekretacji, reconciler, endpointy FastAPI):
```bash
pytest -v
```

---

## 📄 Licencja

Projekt udostępniany na licencji MIT.
