import json
import os
from edgar import Company, set_identity

set_identity("Dhruv d6kapadi@uwaterloo.ca")

companies = {
    "WMT": "Walmart Inc.",
    "COF": "Capital One Financial Corporation",
    "GOOGL": "Alphabet Inc."
}

os.makedirs("data/raw", exist_ok=True) # make a data folder if it doesn't exist

for ticker, name in companies.items():
    print(f"Fetching filings for {name} ({ticker})...")

    filing = Company(ticker).get_filings(form="10-K").latest()
    tenk = filing.obj()

    risk_factors = tenk.risk_factors
    mda = tenk.management_discussion

    print(f'Risk Factors: {len(risk_factors)} characters')
    print(f'Management Discussion and Analysis: {len(mda)} characters')

    records = [
        {"company": name, "ticker": ticker, "section": "Item 1A: Risk Factors", "text": risk_factors},
        {"company": name, "ticker": ticker, "section": "Item 7: Management's Discussion and Analysis", "text": mda}
    ]

    out_path = f'data/raw/{ticker}.json'

    with open(out_path, 'w', encoding = 'utf-8') as f:
        json.dump(records, f, indent=2)

    print(f'Saved to {out_path}\n')

