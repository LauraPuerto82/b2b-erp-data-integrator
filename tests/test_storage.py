from b2b_erp_data_integrator.storage import (
    read_s3_object,
    stream_s3_object,
    write_s3_object,
)


def test_read_s3_object(s3_client, s3_bucket):
    s3_client.put_object(
        Bucket=s3_bucket,
        Key="test-input.txt",
        Body=b"hello from s3",
    )

    content = read_s3_object(
        client=s3_client,
        bucket=s3_bucket,
        key="test-input.txt",
    )

    assert content == b"hello from s3"


def test_write_s3_object(s3_client, s3_bucket):
    write_s3_object(
        client=s3_client,
        bucket=s3_bucket,
        key="test-output.txt",
        content=b"written from boto3",
    )

    content = read_s3_object(
        client=s3_client,
        bucket=s3_bucket,
        key="test-output.txt",
    )

    assert content == b"written from boto3"


def test_stream_s3_object(s3_client, s3_bucket):
    s3_client.put_object(
        Bucket=s3_bucket,
        Key="stream-input.txt",
        Body=b"hello from streaming s3",
    )

    body = stream_s3_object(
        client=s3_client,
        bucket=s3_bucket,
        key="stream-input.txt",
    )

    assert body.read() == b"hello from streaming s3"
