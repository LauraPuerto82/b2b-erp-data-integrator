from b2b_erp_data_integrator.processing.result import RejectedRecord, BatchResult


def test_rejected_record():
    raw_record = {
        "customer_id": "C003",
        "name": "Invalid Corp",
        "tax_id": "B1234",
        "country": "ES",
        "email": "invalid@example.com",
    }

    rejected = RejectedRecord(
        raw_record=raw_record,
        reason="Invalid tax ID for country ES",
    )

    assert rejected.raw_record == raw_record
    assert rejected.reason == "Invalid tax ID for country ES"


def test_batch_result_starts_with_empty_collections():
    result = BatchResult()

    assert result.processed == []
    assert result.rejected == []


def test_batch_results_do_not_share_mutable_collections():
    result1 = BatchResult()
    result2 = BatchResult()

    assert result1.processed is not result2.processed
    assert result1.rejected is not result2.rejected
