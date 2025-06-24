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
import http
import json
import logging
import typing
import quart
from base_view import BaseView, validate_json, ApiResponse
from sql.sql_interface import SqlInterface
import interfaces.cms.project as json_schemas
from state_object import StateObject


class ProjectsApiView(BaseView):
    __slots__ = ['_logger']

    # Allowed fields
    VALID_OVERVIEW_FIELDS = {
        "name"
    }

    VALID_COUNTS_FIELDS = {
        "no_of_milestones",
        "no_of_test_runs"
    }

    DEFAULT_OVERVIEW_FIELDS_LIST = ["name"]

    VALID_TRUE_VALUES = {"true", "1", "yes"}
    VALID_FALSE_VALUES = {"false", "0", "no"}

    def __init__(self, logger: logging.Logger,
                 state_object: StateObject) -> None:
        self._logger = logger.getChild(__name__)
        self._db: SqlInterface = SqlInterface(logger, state_object)

    async def project_details(self, project_id: int):
        details: typing.Optional[dict] = self._db.projects.get_project_details(
            project_id)
        if details is None:
            return quart.Response(json.dumps({}),
                                  status=http.HTTPStatus.BAD_REQUEST,
                                  content_type="application/json")

        return quart.Response(json.dumps(details),
                              status=http.HTTPStatus.OK,
                              content_type="application/json")

    async def project_overviews(self):
        # Get fields from query parameters
        value_fields = quart.request.args.get("value_fields")
        count_fields = quart.request.args.get("count_fields")

        if value_fields:
            requested_fields = value_fields.split(",")

            # Validate requested fields
            invalid_fields = [field for field in requested_fields
                              if field not in self.VALID_OVERVIEW_FIELDS]

            if invalid_fields:
                response_json = {
                    'error': "Invalid value field"
                }
                return quart.Response(json.dumps(response_json),
                                      status=http.HTTPStatus.BAD_REQUEST,
                                      content_type="application/json")

        else:
            requested_fields = list(self.DEFAULT_OVERVIEW_FIELDS_LIST)

        count_no_of_milestones: bool = False
        count_no_of_test_runs: bool = False

        if count_fields:
            requested_count_fields = count_fields.split(",")

            # Validate requested fields
            invalid_fields = [field for field in requested_count_fields
                              if field not in self.VALID_COUNTS_FIELDS]

            if invalid_fields:
                response_json = {
                    'error': "Invalid count field"
                }
                return quart.Response(json.dumps(response_json),
                                      status=http.HTTPStatus.BAD_REQUEST,
                                      content_type="application/json")

            count_no_of_milestones = "no_of_milestones" in count_fields
            count_no_of_test_runs = "no_of_test_runs" in count_fields

        projects: list = []

        requested_fields.insert(0, 'id')
        query_fields = ",".join(requested_fields)

        project_rows = self._db.projects.get_projects_details(query_fields)
        if project_rows is None:
            response_body: dict = {
                "error": "Internal error in CMS"
            }
            return quart.Response(json.dumps(response_body),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        for row in project_rows:
            project: dict = {}

            # Extract project fields from query.
            idx: int = 0
            for row_entry in row:
                project[requested_fields[idx]] = row_entry
                idx += 1

            project_id: int = int(project["id"])
            if count_no_of_milestones:
                project["no_of_milestones"] = \
                    self._db.projects.get_no_of_milestones_for_project(project_id)

            if count_no_of_test_runs:
                project["no_of_test_runs"] = \
                    self._db.projects.get_no_of_testruns_for_project(project_id)

            projects.append(project)

        projects_info: dict = {
            "projects": projects
        }

        return quart.Response(json.dumps(projects_info),
                              status=http.HTTPStatus.OK,
                              content_type="application/json")

    @validate_json(json_schemas.SCHEMA_ADD_PROJECT_REQUEST)
    async def add_project(self, request_msg: ApiResponse):

        name: str = request_msg.body.name

        exists = self._db.projects.project_name_exists(name)
        if exists is None:
            response_body: dict = {
                "status": 0,
                "error_msg": "Internal error in CMS"
            }
            return quart.Response(json.dumps(response_body),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        if exists:
            response_body: dict = {
                "status": 0,
                "error_msg": "Project name already exists"
            }
            return quart.Response(json.dumps(response_body),
                                  status=http.HTTPStatus.BAD_REQUEST,
                                  content_type="application/json")

        add_project_dict: dict = {
            "project_name": name,
            "announcement": request_msg.body.announcement,
            "announcement_on_overview":
                request_msg.body.announcement_on_overview
        }
        new_project_id: typing.Optional[int] = self._db.projects.add_project(
            add_project_dict)
        if new_project_id is None:
            response_body: dict = {
                "status": 0,
                "error_msg": "Internal SQL error in CMS"
            }
            return quart.Response(json.dumps(response_body),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        response_body: dict = {"project_id": new_project_id}
        return quart.Response(json.dumps(response_body),
                              status=http.HTTPStatus.OK,
                              content_type="application/json")

    @validate_json(json_schemas.SCHEMA_MODIFY_PROJECT_REQUEST)
    async def modify_project(self, request_msg: ApiResponse, project_id: int):
        """
        Modify the details of an existing project based on the provided project
        ID.

        Args:
            request_msg (ApiResponse): The request message containing the
                                       updated project details.
            project_id (int): The ID of the project to be modified.

        Returns:
            quart.Response:
                - HTTP 200 (OK) with `{"status": 1}` if the project is
                  successfully updated.
                - HTTP 400 (Bad Request) if the requested project name already
                  exists.
                - HTTP 500 (Internal Server Error) if an internal error occurs.

        Behavior:
            - Validates the input using the `SCHEMA_MODIFY_PROJECT_REQUEST`.
            - Checks if the project with the given `project_id` exists.
            - If the project does not exist, returns an internal error response.
            - If the project name is being changed, checks for name conflicts.
            - If a conflict is detected, returns a 400 error.
            - Updates the project details using the database method
              `self._db.modify_project`.

        Errors:
            - Logs and returns an internal error if database queries fail.
            - Returns a bad request error if the new project name already exists.

        Example Response:
            ```json
            {
                "status": 1
            }
            ```
        """
        existing_details = self._db.projects.get_project_details(project_id)
        if existing_details is None:
            response_body: dict = {
                "status": 0,
                "error_msg": "Internal error : Cannot get project details"
            }
            self._logger.warning("modify_project: Cannot get project details")
            return quart.Response(json.dumps(response_body),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        elif not existing_details:
            response_body: dict = {
                "status": 0,
                "error_msg": "Invalid project ID"
            }
            return quart.Response(json.dumps(response_body),
                                  status=http.HTTPStatus.BAD_REQUEST,
                                  content_type="application/json")

        body = request_msg.body
        updated_details = {
            "announcement": body.announcement,
            "announcement_on_overview": body.announcement_on_overview
        }

        if body.name != existing_details["name"]:
            exists = self._db.projects.project_name_exists(body.name)

            if exists is None:
                response_body: dict = {
                    "status": 0,
                    "error_msg": "Internal error : Cannot check project name"
                }
                self._logger.warning("modify_project: Cannot check project name")
                return quart.Response(json.dumps(response_body),
                                      status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                      content_type="application/json")

            if exists:
                response_body: dict = {
                    "status": 0,
                    "error_msg": "New project name already exists"
                }
                return quart.Response(json.dumps(response_body),
                                      status=http.HTTPStatus.BAD_REQUEST,
                                      content_type="application/json")

            updated_details["project_name"] = body.name

        status = self._db.projects.modify_project(project_id, updated_details)

        return quart.Response(json.dumps({ "status": 1}),
                              status=http.HTTPStatus.OK,
                              content_type="application/json")

    async def delete_project(self, project_id: int):

        hard_delete_param = quart.request.args.get("hard_delete")

        if hard_delete_param is None:
            hard_delete: bool = False  # Default value

        else:
            hard_delete_lower = hard_delete_param.lower()
            if hard_delete_lower in self.VALID_TRUE_VALUES:
                hard_delete: bool = True
            elif hard_delete_lower in self.VALID_FALSE_VALUES:
                hard_delete: bool = False
            else:
                response_body: dict = {
                    "status": 0,
                    "error_msg": "Invalid parameter for hard_delete argument"
                }
                return quart.Response(json.dumps(response_body),
                                      status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                      content_type="application/json")

        exists = self._db.projects.is_valid_project_id(project_id)
        if exists is None:
            response_body: dict = {
                "status": 0,
                "error_msg": "Internal error in CMS"
            }
            return quart.Response(json.dumps(response_body),
                                  status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                  content_type="application/json")

        if not exists:
            response_body: dict = {
                "status": 0,
                "error_msg": "Project id is invalid"
            }
            return quart.Response(json.dumps(response_body),
                                  status=http.HTTPStatus.BAD_REQUEST,
                                  content_type="application/json")

        if hard_delete:
            self._logger.info("Project %d is being hard-deleted", project_id)
            if not self._db.projects.hard_delete_project(project_id):
                response_body: dict = {
                    "status": 0,
                    "error_msg": "Internal error in CMS"
                }
                return quart.Response(json.dumps(response_body),
                                      status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                      content_type="application/json")

        else:
            self._logger.info("Project %d is being marked as 'awaiting purge",
                              project_id)
            if not self._db.projects.mark_project_for_awaiting_purge(project_id):
                response_body: dict = {
                    "status": 0,
                    "error_msg": "Internal error in CMS"
                }
                return quart.Response(json.dumps(response_body),
                                      status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                                      content_type="application/json")

        return quart.Response(json.dumps({}),
                              status=http.HTTPStatus.OK,
                              content_type="application/json")
