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
