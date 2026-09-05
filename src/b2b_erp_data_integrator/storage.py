from pathlib import Path


def read_s3_object(
    client,
    bucket: str,
    key: str,
) -> bytes:
    response = client.get_object(
        Bucket=bucket,
        Key=key,
    )

    return response["Body"].read()


def write_s3_object(
    client,
    bucket: str,
    key: str,
    content: bytes,
) -> None:
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=content,
    )


def stream_s3_object(
    client,
    bucket: str,
    key: str,
):
    response = client.get_object(
        Bucket=bucket,
        Key=key,
    )

    return response["Body"]


def upload_s3_file(
    client,
    bucket: str,
    key: str,
    path: Path,
) -> None:
    client.upload_file(
        str(path),
        bucket,
        key,
    )
