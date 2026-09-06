from b2b_erp_data_integrator.spark.ingestion import read_csv_dataframe


def test_read_csv_dataframe(tmp_path, spark_session):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "client_code,legal_name,vat_number,country,contact_email\n"
        "0001,ACME S.L.,ESB12345678,Spain,info@acme.es\n",
        encoding="utf-8",
    )

    dataframe = read_csv_dataframe(
        spark=spark_session,
        path=str(csv_path),
    )

    row = dataframe.first()

    assert row is not None
    assert dataframe.columns == [
        "client_code",
        "legal_name",
        "vat_number",
        "country",
        "contact_email",
    ]
    assert row.client_code == "0001"
    assert row.legal_name == "ACME S.L."
    assert row.vat_number == "ESB12345678"
    assert row.country == "Spain"
    assert row.contact_email == "info@acme.es"
