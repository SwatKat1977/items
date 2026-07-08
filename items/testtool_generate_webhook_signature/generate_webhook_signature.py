import argparse
import hashlib
import hmac
import json
import sys
import uuid


def generate_api_signature(secret_key: bytes,
                           data: dict | str | bytes) -> str:
    """
    Generates an api HMAC-SHA256 signature for the given data using the
    provided secret key.

    Args:
        secret_key (bytes): The secret key used for HMAC generation.
        data (dict | str | bytes): The data to be signed.

    Returns:
        str: The generated HMAC signature as a hexadecimal string.
    """
    if isinstance(data, dict):
        # Convert dictionary to JSON string
        data = json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')
    elif isinstance(data, str):
        data = data.encode('utf-8')  # Ensure it's in bytes
    elif isinstance(data, bytes):
        pass  # Already in bytes
    else:
        raise TypeError("Data must be a str, bytes, or dict")

    return hmac.new(secret_key, data, hashlib.sha256).hexdigest()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an HMAC-SHA256 API signature for the given data.")
    parser.add_argument(
        "-s", "--secret",
        required=True,
        help="The secret key used for HMAC generation (e.g. ApiSigningSecret).")
    parser.add_argument(
        "-d", "--data",
        help="The data to sign. If omitted, a random UUID is generated and used.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Treat the data as JSON: parse it and sign a canonical "
             "(sorted, compact) representation.")
    return parser.parse_args(argv)


def verify_api_signature(secret_key: bytes,
                         data: dict | str | bytes,
                         received_signature: str) -> bool:
    """
    Verifies the integrity and authenticity of received data using
    HMAC-SHA256.

    Args:
        secret_key (bytes): The secret key used for HMAC generation.
        data (dict | str | bytes): The data to be verified.
        received_signature (str): The expected HMAC signature.

    Returns:
        bool: True if the computed api signature matches the received
              signature, False otherwise.
    """
    if isinstance(data, dict):
        data = json.dumps(data, separators=(',', ':'), sort_keys=True).encode('utf-8')
    elif isinstance(data, str):
        data = data.encode('utf-8')
    elif isinstance(data, bytes):
        pass
    else:
        raise TypeError("Data must be a str, bytes, or dict")

    computed_signature = hmac.new(secret_key, data, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed_signature, received_signature)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # Use --data if given, otherwise generate a random UUID and use that.
    if args.data is not None:
        raw_data = args.data
    else:
        raw_data = str(uuid.uuid4())


    if args.json:
        try:
            data: dict | str = json.loads(raw_data)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON data: {exc}", file=sys.stderr)
            return 1
    else:
        data = raw_data

    print(f"NONCE          : {raw_data}")

    data: bytes = f"/web/webhook/metadata:{data}".encode("utf-8")
    print(f"Signature Data : {data}")
    secret_key: bytes = args.secret.encode('utf-8')
    print(f"Secret Key     : {secret_key} ")
    signature = generate_api_signature(args.secret.encode('utf-8'), data)
    print(f"signature      : {signature}")

    #verified: bool = verify_api_signature()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
