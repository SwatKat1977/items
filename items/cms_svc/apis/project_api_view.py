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
import quart
from base_view import BaseView
from sqlite_interface import SqliteInterface


class ProjectApiView(BaseView):
    __slots__ = ['_logger']

    # Allowed fields
    VALID_OVERVIEW_FIELDS = {
        "name"
    }

    VALID_OVERVIEW_COUNTS = {
        "no_of_milestones",
        "no_of_test_runs"
    }

    DEFAULT_OVERVIEW_FIELDS_LIST = ["name"]

    def __init__(self, logger: logging.Logger, db: SqliteInterface) -> None:
        self._logger = logger.getChild(__name__)
        self._db: SqliteInterface = db

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
                    'error': "Invalid field"
                }
                return quart.Response(json.dumps(response_json),
                                      status=http.HTTPStatus.BAD_REQUEST,
                                      content_type="application/json")

        else:
            requested_fields = list(self.DEFAULT_OVERVIEW_FIELDS_LIST)

        count_no_of_milestones: bool = False
        count_no_of_test_runs: bool = False

        if count_fields:
            count_no_of_milestones = "no_of_milestones" in count_fields
            count_no_of_test_runs = "no_of_test_runs" in count_fields

        projects: list = []

        requested_fields.insert(0, 'id')
        query_fields = ",".join(requested_fields)

        project_rows = self._db.get_projects_details(query_fields)
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
                    self._db.get_no_of_milestones_for_project(project_id)

            if count_no_of_test_runs:
                project["no_of_test_runs"] = \
                    self._db.get_no_of_testruns_for_project(project_id)

            projects.append(project)

        projects_info: dict = {
            "projects": projects
        }

        return quart.Response(json.dumps(projects_info),
                              status=http.HTTPStatus.OK,
                              content_type="application/json")
