import pytest

from b2b_erp_data_integrator.integrations.erp_a.customer import map_erp_a_customer
from b2b_erp_data_integrator.processing.customer import process_customers


def test_process_customers_continues_after_rejected_record():
    record1 = {
        "customer_id": "C001",
        "name": "Valid Corp 1",
        "tax_id": "B12345678",
        "country": "ES",
        "email": "valid_one@example.com",
    }

    record2 = {
        "customer_id": "C002",
        "name": "Invalid Corp",
        "tax_id": "B1234",
        "country": "ES",
        "email": "invalid@example.com",
    }

    record3 = {
        "customer_id": "C003",
        "name": "Valid Corp 2",
        "tax_id": "B87654321",
        "country": "ES",
        "email": "valid_two@example.com",
    }

    data = [record1, record2, record3]

    result = process_customers(data, map_erp_a_customer)

    assert len(result.processed) == 2
    assert len(result.rejected) == 1
    assert result.rejected[0].raw_record == record2
    assert result.rejected[0].reason == "Invalid tax ID for country ES"


def test_process_customers_propagates_unexpected_mapper_errors():
    record = {
        "customer_id": "C001",
        "name": "Valid Corp",
        "tax_id": "B12345678",
        "country": "ES",
        "email": "valid@example.com",
    }

    def broken_mapper(record: dict):
        raise RuntimeError("Unexpected mapper failure")

    with pytest.raises(RuntimeError, match="Unexpected mapper failure"):
        process_customers([record], broken_mapper)


def test_process_customers_propagates_unexpected_value_errors():
    record = {
        "customer_id": "C001",
        "name": "Valid Corp",
        "tax_id": "B12345678",
        "country": "ES",
        "email": "valid@example.com",
    }

    def broken_mapper(record: dict):
        raise ValueError("Unexpected technical failure")

    with pytest.raises(ValueError, match="Unexpected technical failure"):
        process_customers([record], broken_mapper)


def test_process_customers_accepts_iterator():
    records = iter(
        [
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
    )

    result = process_customers(records, map_erp_a_customer)

    assert len(result.processed) == 2
    assert len(result.rejected) == 0
