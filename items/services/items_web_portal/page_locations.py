"""
Copyright 2025-2026 Integrated Test Management Suite Development Team
Copyright 2017-2025 INTMAC Development Team [Defunct]

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

# Login page template
TEMPLATE_LOGIN_PAGE: str = "login.html"

# Account setup page reached from an invitation email link
PAGE_ACCEPT_INVITE: str = "accept_invite.html"

# Dashboard page template
TEMPLATE_DASHBOARD_PAGE: str = "dashboard.html"

# Test definitions page template
TEMPLATE_TEST_DEFINITIONS_PAGE: str = "project_testcases.html"

# Internal error page template
TEMPLATE_INTERNAL_ERROR_PAGE: str = "internal_server_error.html"


#####
# Pages for projects
#####

PAGE_PROJECT_OVERVIEW: str = "project_overview.html"

#####
# Pages for instance administration
#####

PAGE_INSTANCE_ADMIN_OVERVIEW: str = "instance_admin_overview.html"
PAGE_INSTANCE_ADMIN_PROJECTS: str = "instance_admin_projects.html"
PAGE_INSTANCE_ADMIN_USERS_AND_ROLES: str = "instance_admin_users_roles.html"
PAGE_INSTANCE_ADMIN_MANAGE_DATA: str = "instance_admin_manage_data.html"
PAGE_INSTANCE_ADMIN_CUSTOMISATIONS: str = "instance_admin_customisations.html"
PAGE_INSTANCE_ADMIN_INTEGRATIONS: str = "instance_admin_integrations.html"
PAGE_INSTANCE_ADMIN_SITE_SETTINGS: str = "instance_admin_site_settings.html"

PAGE_INSTANCE_ADMIN_ADD_PROJECT: str = "instance_admin_add_project.html"
PAGE_INSTANCE_ADMIN_MODIFY_PROJECT: str = "instance_admin_modify_project.html"

PAGE_INSTANCE_ADMIN_ADD_USER: str = "instance_admin_add_user.html"
PAGE_INSTANCE_ADMIN_MODIFY_USER: str = "instance_admin_modify_user.html"
PAGE_INSTANCE_ADMIN_RESET_PASSWORD: str = "instance_admin_reset_password.html"
