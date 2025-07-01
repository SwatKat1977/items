# 📘 API Documentation

This document describes the API routes available in the Quart application. Routes are grouped by category (Blueprint). Each endpoint includes its method, path, purpose, and expected behavior.

---

## 🩺 Health API

**Blueprint Name**: `health_api`  
**Base URL**: /health

### `GET /status`

- **Description**: Returns a health check response indicating the service is operational.
- **Response**:
  ```json
  {
    "status": "ok"
  }
  