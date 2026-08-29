COUNTRY_CODES = {
    "Spain": "ES",
    "France": "FR",
    "Germany": "DE",
}


def normalize_country(value: str) -> str:
    if value in COUNTRY_CODES.values():
        return value

    return COUNTRY_CODES[value]
