from b2b_erp_data_integrator.normalization.country import normalize_country


def test_normalize_country_name_to_iso_code():
    assert normalize_country("Spain") == "ES"