def normalize_tax_id(value: str, country: str) -> str:
    normalized = value.strip().upper()
    normalized = normalized.replace("-", "").replace(" ", "")
    normalized = normalized.removeprefix(country)

    return normalized
