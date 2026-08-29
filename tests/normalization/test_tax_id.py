from b2b_erp_data_integrator.normalization.tax_id import normalize_tax_id


def test_normalize_tax_id_without_changes():
    assert normalize_tax_id("B12345678", country="ES") == "B12345678"


def test_normalize_tax_id_removes_country_prefix():
    assert normalize_tax_id("ESB12345678", country="ES") == "B12345678"


def test_normalize_tax_id_removes_hyphen():
    assert normalize_tax_id("B-12345678", country="ES") == "B12345678"


def test_normalize_tax_id_converts_to_uppercase():
    assert normalize_tax_id("b12345678", country="ES") == "B12345678"


def test_normalize_tax_id_removes_spaces():
    assert normalize_tax_id("B 12345678", country="ES") == "B12345678"
