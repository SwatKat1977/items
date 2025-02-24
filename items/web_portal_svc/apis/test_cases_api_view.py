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
from base_web_view import BaseWebView
import page_locations as pages

class TestCasesApiView(BaseWebView):

    def __init__(self, logger):
        super().__init__(logger)

    async def test_cases(self, project_id: int):
        # Sample data (replace this with your actual data)
        data = [
            [
                0,  # Indentation level
                1,  # Folder ID
                "Functional Tests",  # Folder name
                [  # Files in this folder
                    {"id": 5, "name": "Invalid Login Test"},
                    {"id": 4, "name": "Valid Login Test"}
                ]
            ],
            [
                1,  # Indentation level
                2,  # Folder ID
                "Performance Tests",  # Folder name
                [  # Files in this folder
                    {"id": 6, "name": "Load Test"},
                    {"id": 7, "name": "Stress Test"}
                ]
            ]
        ]

        page = "test-cases"  # Default to 'Overview'
        return await self._render_page(pages.TEMPLATE_TEST_DEFINITIONS_PAGE,
                                       data=data, active_page=page,
                                       has_testcases=True)
