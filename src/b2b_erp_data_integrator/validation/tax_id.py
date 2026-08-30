def validate_tax_id(tax_id: str, country: str) -> bool:
    if country == "ES":
        return len(tax_id) == 9

    return True
