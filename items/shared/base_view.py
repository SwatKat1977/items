'''
Copyright 2014-2025 Integrated Test Management Suite

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
from dataclasses import dataclass
import json
import http
from types import SimpleNamespace
import typing
import aiohttp
import jsonschema

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

class BaseView:
    """ Base view class """
    # pylint: disable=too-few-public-methods

    ERR_MSG_INVALID_BODY_TYPE : str = "Invalid body type, not JSON"
    ERR_MSG_MISSING_INVALID_JSON_BODY : str = "Missing/invalid json body"
    ERR_MSG_BODY_SCHEMA_MISMATCH : str = "Message body failed schema validation"

    CONTENT_TYPE_JSON : str = 'application/json'
    CONTENT_TYPE_TEXT : str = 'text/plain'

    def _validate_json_body(self, data : str, json_schema : dict = None) \
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

    async def _call_api_post(self, url : str, json_data : dict = None) -> ApiResponse:
        """
        Make an API call using the POST method.

        parameters:
            url - URL of the endpoint
            json_data - Optional Json body.

        returns:
            ApiResponse which will will contain response data or just
            exception_msg if something went wrong.
        """

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=json_data) as resp:
                    body = await resp.json() \
                        if resp.content_type == self.CONTENT_TYPE_JSON \
                        else await resp.text()
                    api_return = ApiResponse(
                        status_code = resp.status,
                        body = body,
                        content_type = resp.content_type)

        except (aiohttp.ClientConnectionError, aiohttp.ClientError) as ex:
            api_return = ApiResponse(exception_msg = ex)

        return api_return

    async def _call_api_get(self, url : str, json_data : dict = None) -> ApiResponse:
        """
        Make an API call using the GET method.

        parameters:
            url - URL of the endpoint
            json_data - Optional Json body.

        returns:
            ApiResponse which will will contain response data or just
            exception_msg if something went wrong.
        """

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, json=json_data) as resp:
                    body = await resp.json() \
                        if resp.content_type == self.CONTENT_TYPE_JSON \
                        else await resp.text()
                    api_return = ApiResponse(
                        status_code = resp.status,
                        body = body,
                        content_type = resp.content_type)

        except (aiohttp.ClientConnectionError, aiohttp.ClientError) as ex:
            api_return = ApiResponse(exception_msg = ex)

        return api_return
