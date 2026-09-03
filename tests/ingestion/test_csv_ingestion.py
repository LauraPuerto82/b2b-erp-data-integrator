from pathlib import Path

from b2b_erp_data_integrator.ingestion import (
    read_csv,
    read_csv_fields,
)
from b2b_erp_data_integrator.integrations.erp_a.customer import (
    map_erp_a_customer,
)
from b2b_erp_data_integrator.processing.customer import process_customers


def test_read_csv_returns_records(tmp_path: Path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "customer_id,name,tax_id,country,email\n"
        "C001,ACME SL,B12345678,ES,info@acme.es\n"
        "C002,Globex SL,A87654321,ES,contact@globex.es\n",
        encoding="utf-8",
    )

    records = list(read_csv(csv_path))

    assert records == [
        {
            "customer_id": "C001",
            "name": "ACME SL",
            "tax_id": "B12345678",
            "country": "ES",
            "email": "info@acme.es",
        },
        {
            "customer_id": "C002",
            "name": "Globex SL",
            "tax_id": "A87654321",
            "country": "ES",
            "email": "contact@globex.es",
        },
    ]


def test_csv_records_can_be_processed(tmp_path: Path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "customer_id,name,tax_id,country,email\n"
        "C001,ACME SL,B12345678,ES,info@acme.es\n"
        "C002,Globex SL,A87654321,ES,contact@globex.es\n",
        encoding="utf-8",
    )

    records = read_csv(csv_path)

    result = process_customers(records, map_erp_a_customer)

    assert len(result.processed) == 2
    assert len(result.rejected) == 0

    assert result.processed[0].customer.name == "ACME SL"
    assert result.processed[1].customer.name == "Globex SL"


def test_read_csv_fields_returns_header_fields(tmp_path: Path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "client_code,legal_name,vat_number,country,contact_email\n"
        "0001,ACME S.L.,ESB12345678,Spain,info@acme.es\n",
        encoding="utf-8",
    )

    fields = read_csv_fields(csv_path)

    assert fields == {
        "client_code",
        "legal_name",
        "vat_number",
        "country",
        "contact_email",
    }
