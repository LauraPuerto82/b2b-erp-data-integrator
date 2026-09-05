import boto3  # type: ignore[import-untyped]
import pytest


@pytest.fixture
def s3_client():
    client = boto3.client(
        "s3",
        endpoint_url="http://localhost:4566",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
    )

    return client


@pytest.fixture
def s3_bucket(s3_client):
    bucket = "b2b-erp-data-integrator-test"

    existing_buckets = {
        existing_bucket["Name"]
        for existing_bucket in s3_client.list_buckets()["Buckets"]
    }

    if bucket not in existing_buckets:
        s3_client.create_bucket(Bucket=bucket)

    return bucket
