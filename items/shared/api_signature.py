"""
Copyright 2025-2026 Integrated Test Management Suite Development Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import hashlib
import hmac
import json


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
