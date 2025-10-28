# API Documentation

This document describes the API routes available in the Quart application. Routes are grouped by category (Blueprint). Each endpoint includes its method, path, purpose, and expected behavior.

---

## Health API

**Blueprint Name**: `health_api`  
**Base URL**: /health

### `GET /status`

- **Description**: Returns a health check response indicating the service is operational.
- **Response**:
  ```json
  {
    "status": "ok"
  }
  
## Projects API

**Blueprint Name**: `project_api`  
**Base URL**: /projects

### `GET /details/<int:project_id>`

- **Description**: Returns details for a project.

### `GET /overviews`

- **Description**: Get a list of projects

### `/add`

- **Description**: Add a new project

### `POST /modify/<int:project_id>`

- **Description**: Add a new project

### `DELETE /delete/<int:project_id>`

- **Description**: Delete a new project. If the field hard_delete=false then
                   the project is only marked to be purged in the future, where
                   true will result in the project and any related test cases to
                   be deleted. Projects marked for purging don't appear in searches.

