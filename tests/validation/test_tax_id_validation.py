from b2b_erp_data_integrator.validation.tax_id import validate_tax_id


def test_valid_spanish_tax_id():
    assert validate_tax_id("B12345678", country="ES") is True


def test_invalid_spanish_tax_id():
    assert validate_tax_id("B1234", country="ES") is False
