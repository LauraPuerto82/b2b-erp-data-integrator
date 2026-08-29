COUNTRY_CODES = {
    "Spain": "ES",
    "France": "FR",
    "Germany": "DE",
}


def normalize_country(value: str) -> str:
    return COUNTRY_CODES[value]
