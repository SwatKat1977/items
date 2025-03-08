"""
Copyright 2025 Integrated Test Management Suite Development Team

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
import asyncio
from dataclasses import dataclass
from functools import wraps
import hashlib
import hmac
import json
import http
from types import SimpleNamespace
import typing
import aiohttp
import jsonschema
import quart
import requests


@dataclass(init=True)
class ApiResponse:
    """ Class for keeping track of api return data. """
    status_code: int
    body: dict | str
    content_type : str
    exception_msg : str

    def __init__(self,
                 status_code: int = 0,
                 body: dict | str = None,
                 content_type : str = None,
                 exception_msg : str = None):
        self.status_code = status_code
        self.body = body
        self.content_type = content_type
        self.exception_msg = exception_msg


def validate_json(schema):
    """
    Decorator to validate the JSON request body against a given schema.

    This decorator:
    - Extracts and validates the JSON request body using the provided schema.
    - If validation fails, returns an HTTP 500 response with an error message.
    - If validation succeeds, passes the validated data (`request_msg`) to the wrapped function.

    Args:
        schema (dict): The JSON schema to validate the request body against.

    Returns:
        A Quart Response object in case of validation failure,
        otherwise, the decorated function is called with the validated data.

    Example:
        @validate_json(handshake_api.SCHEMA_BASIC_AUTHENTICATE_REQUEST)
        async def basic_authenticate(self, request_msg: ApiResponse) -> Response:
            return Response(json.dumps({"status": 1, "message": "Success"}),
                            status=HTTPStatus.OK,
                            content_type="application/json")
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                # Validate the JSON body using the provided schema
                request_msg: ApiResponse = self.validate_json_body(
                    await quart.request.get_data(),
                    schema
                )

                # If validation fails, return an error response
                if request_msg.status_code != http.HTTPStatus.OK:
                    response_json = {
                        'status': 0,
                        'error': request_msg.exception_msg
                    }
                    return quart.Response(
                        json.dumps(response_json),
                        status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                        content_type="application/json"
                    )

                # If validation passes, call the original function
                return await func(self, request_msg, *args, **kwargs)


            except jsonschema.exceptions.ValidationError as e:
                error_msg = f"Schema validation error: {str(e)}"

            except json.JSONDecodeError as e:
                error_msg = f"JSON decoding error: {str(e)}"

            except requests.exceptions.ConnectionError as e:
                error_msg = f"Connection error: {str(e)}"

            except TypeError as e:
                error_msg = f"Type error: {str(e)}"

            # Catch specific errors and return an internal server error response
            response_json = {
                'status': 0,
                'error': error_msg
            }
            return quart.Response(
                json.dumps(response_json),
                status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type="application/json"
            )

        return wrapper
    return decorator


class BaseView:
    """ Base view class """
    # pylint: disable=too-few-public-methods

    ERR_MSG_INVALID_BODY_TYPE : str = "Invalid body type, not JSON"
    ERR_MSG_MISSING_INVALID_JSON_BODY : str = "Missing/invalid json body"
    ERR_MSG_BODY_SCHEMA_MISMATCH : str = "Message body failed schema validation"

    CONTENT_TYPE_JSON : str = 'application/json'
    CONTENT_TYPE_TEXT : str = 'text/plain'

    def validate_json_body(self, data: str, json_schema: dict = None) \
            -> typing.Optional[ApiResponse]:
        """
        This is a temporary work around as changing _validate_json_body*()
        would be fairly breaking. This needs to be fixed!
        """
        return self._validate_json_body(data, json_schema)

    def _validate_json_body(self, data: str, json_schema: dict = None) \
            -> typing.Optional[ApiResponse]:
        """
        Validate response body is JSON.

        NOTE: This has not been optimised, it can and should be in the future!

        parameters:
            data : Response body to validate.
            json_schema : Optional Json schema to validate the body against.

        returns:
            ApiResponse : If successful then object is a valid object.
        """

        if data is None:
            return ApiResponse(exception_msg=self.ERR_MSG_MISSING_INVALID_JSON_BODY,
                               status_code=http.HTTPStatus.BAD_REQUEST,
                               content_type=self.CONTENT_TYPE_TEXT)

        try:
            json_data = json.loads(data)

        except (TypeError, json.JSONDecodeError):
            return ApiResponse(exception_msg=self.ERR_MSG_INVALID_BODY_TYPE,
                               status_code=http.HTTPStatus.BAD_REQUEST,
                               content_type=self.CONTENT_TYPE_TEXT)

        # If there is a JSON schema then validate that the json body conforms
        # to the expected schema. If the body isn't valid then a 400 error
        # should be generated.
        if json_schema:
            try:
                jsonschema.validate(instance=json_data,
                                    schema=json_schema)

            except jsonschema.exceptions.ValidationError:
                return ApiResponse(exception_msg=self.ERR_MSG_BODY_SCHEMA_MISMATCH,
                                   status_code=http.HTTPStatus.BAD_REQUEST,
                                   content_type=self.CONTENT_TYPE_TEXT)

        return ApiResponse(body=json.loads(
            data, object_hook=lambda d: SimpleNamespace(**d)),
                           status_code=http.HTTPStatus.OK,
                           content_type=self.CONTENT_TYPE_JSON)

    async def _call_api_post(self, url: str,
                             json_data: dict = None,
                             timeout: int = 2) -> ApiResponse:
        """
        Make an API call using the POST method.

        parameters:
            url - URL of the endpoint
            json_data - Optional Json body.

        returns:
            ApiResponse which will contain response data or just
            exception_msg if something went wrong.
        """

        try:
            async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.post(url, json=json_data) as resp:
                    body = await resp.json() \
                        if resp.content_type == self.CONTENT_TYPE_JSON \
                        else await resp.text()
                    api_return = ApiResponse(
                        status_code=resp.status,
                        body=body,
                        content_type=resp.content_type)

        except (aiohttp.ClientConnectionError, aiohttp.ClientError) as ex:
            api_return = ApiResponse(exception_msg=str(ex))

        except asyncio.TimeoutError as ex:
            api_return = ApiResponse(exception_msg=str(ex))

        return api_return

    async def _call_api_get(self, url: str,
                            json_data: dict = None,
                            timeout: int = 2) -> ApiResponse:
        """
        Make an API call using the GET method.

        parameters:
            url - URL of the endpoint
            json_data - Optional Json body.

        returns:
            ApiResponse which will contain response data or just
            exception_msg if something went wrong.
        """

        try:
            async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url, json=json_data) as resp:
                    body = await resp.json() \
                        if resp.content_type == self.CONTENT_TYPE_JSON \
                        else await resp.text()
                    api_return = ApiResponse(
                        status_code = resp.status,
                        body = body,
                        content_type = resp.content_type)

        except (aiohttp.ClientConnectionError, aiohttp.ClientError) as ex:
            api_return = ApiResponse(exception_msg=ex)

        except asyncio.TimeoutError as ex:
            api_return = ApiResponse(exception_msg=str(ex))

        return api_return

    def verify_api_signature(self,
                             secret_key: bytes,
                             data: any, received_signature) -> bool:
        """
        Verifies the integrity and authenticity of received data using
        HMAC-SHA256.

        Args:
            secret_key (bytes): The secret key used for HMAC generation.
            data (any): The data to be verified.
            received_signature (str): The expected HMAC signature.

        Returns:
            bool: True if the computed api signature matches the received
                  signature, False otherwise.
        """
        computed_signature = hmac.new(secret_key, data, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed_signature, received_signature)

    def generate_api_signature(self, secret_key: bytes, data: any):
        """
        Generates an api HMAC-SHA256 signature for the given data using the
        provided secret key.

        Args:
            secret_key (bytes): The secret key used for HMAC generation.
            data (str): The data to be signed.

        Returns:
            str: The generated HMAC signature as a hexadecimal string.
        """
        return hmac.new(secret_key, data.encode(), hashlib.sha256).hexdigest()
