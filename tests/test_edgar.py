from edgar import Company, set_identity

set_identity("Dhruv d6kapadi@uwaterloo.ca")

company = Company("WMT")
filing = company.get_filings(form="10-K").latest()

print(f"Company: {filing.company}")
print(f"Form: {filing.form}")
print(f"Filing date: {filing.filing_date}")

text = filing.text()
print(f"Total characters: {len(text)}")
print(text[:500])