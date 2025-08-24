# GEMINI.md

# 📌 Project Update (August 24, 2025)

---

### Frontend Changes (August 24, 2025)

This update introduces **edit** and **delete** functionality for devices in the frontend.

#### New Components

- **`frontend/src/components/DeviceForm.tsx`**
  - Reusable form for both **adding** and **editing** device details.
  - Handles inputs for: `name`, `type`, `IP address`, `port`, `username`, `password`, `secret`.
  - During editing, password and secret are **optional**.

#### Modified Pages

- **`frontend/src/pages/AddDevicePage.tsx`**
  - Refactored to use `DeviceForm.tsx` for creating devices.

- **`frontend/src/pages/EditDevicePage.tsx`** _(new)_
  - Fetches device data from API based on URL parameter (`/devices/edit/:id`).
  - Populates `DeviceForm.tsx` for editing.
  - Submits changes via **`PUT`** request to backend API.

- **`frontend/src/pages/DeviceListPage.tsx`**
  - Added `onClick` handlers for "Edit" and "Delete".
  - **Edit** → navigates to `/devices/edit/:id`.
  - **Delete** → confirmation dialog, then sends **`DELETE`** request to backend API.
  - Updates device list on successful deletion.

#### Routing Updates

- **`frontend/src/App.tsx`**
  - Added new route:

    ```tsx
    <Route path="/devices/edit/:id" element={<EditDevicePage />} />
    ```

  - Enables navigation to device editing interface.

---

### Project Overview

This project is a **Software-Defined Networking (SDN) Controller API** built with Python and FastAPI.  
It provides a RESTful interface to manage and interact with network devices from various vendors.

- Modular, object-oriented design.
- Device controllers for specific types (e.g., Cisco IOS, Juniper Junos).
- SQLAlchemy for DB interactions, Netmiko for device automation, Redis for caching.

---

### Key Technologies

- **Backend:** Python, FastAPI
- **Database:** SQLAlchemy, PostgreSQL (psycopg2)
- **Device Automation:** Netmiko
- **Caching:** Redis
- **Authentication:** JWT
- **Testing:** Pytest

---

### Architecture

- **`main.py`**: FastAPI entry point.
- **`src/database.py`**: Database connection + session.
- **`src/models.py`**: SQLAlchemy models.
- **`src/schemas.py`**: Pydantic schemas.
- **`src/crud.py`**: Database CRUD logic.
- **`src/controllers/`**: Vendor-specific device controllers.
- **`src/api/`**: FastAPI routers and endpoints.
- **`src/security.py`**: Authentication + password hashing.
- **`src/tasks.py`**: Scheduler for unknown device update.
- **`src/config.py`**: Application settings and environment.

---

### Building and Running

#### Prerequisites

- Python 3.12+
- PostgreSQL
- Redis

#### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

