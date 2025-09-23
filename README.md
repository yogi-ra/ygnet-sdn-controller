# SDN Controller API

## Project Overview

This project is a **Software-Defined Networking (SDN) Controller API** built with Python and FastAPI. 
It provides a RESTful interface to manage and interact with network devices from various vendors.

- Modular, object-oriented design.
- Device controllers for specific types (e.g., Cisco IOS, Juniper Junos).
- SQLAlchemy for DB interactions, Netmiko for device automation, Redis for caching.

## Key Technologies

- **Backend:** Python, FastAPI
- **Database:** SQLAlchemy, PostgreSQL (psycopg2)
- **Device Automation:** Netmiko
- **Caching:** Redis
- **Authentication:** JWT
- **Testing:** Pytest
- **Asynchronous Processing:** Celery, Redis

## Architecture

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
- **`src/celery_app.py`**: Celery application configuration.
- **`src/tasks.py`**: Celery tasks for asynchronous device command execution.

## Supported Device Types

- **Cisco IOS Router** (`cisco_ios_router`): For Cisco routers running IOS.
- **Cisco IOS Switch** (`cisco_ios_switch`): For Cisco switches running IOS.
- **Juniper Junos** (`juniper_junos`): For Juniper devices running Junos.
- **Aruba ProCurve** (`aruba_procurve`): For Aruba ProCurve switches.
- **Ubiquiti EdgeRouter** (`ubiquiti_edgerouter`): For Ubiquiti EdgeRouter devices.
- **Ubiquiti EdgeSwitch** (`ubiquiti_edgeswitch`): For Ubiquiti EdgeSwitch devices.
- **Ubiquiti UniFi Switch** (`ubiquiti_unifiswitch`): For Ubiquiti UniFi switches (e.g., USW-Lite-8-POE).

## API Endpoints for Frontend Developers

- **`GET /api/devices/supported-features`**: Returns a mapping of device types to their supported features. This endpoint helps frontend developers understand what features are available for each device type.
- **Device-type specific views**: The frontend implements static views for specific device types (e.g., Cisco IOS Router, Cisco IOS Switch) to improve performance and maintainability.

## Asynchronous Architecture

To improve scalability and prevent API timeouts from long-running device commands, the backend uses a job queue system with Celery and Redis. This changes the command execution from a synchronous (blocking) model to an asynchronous (non-blocking) one.

### How It Works

1. **Job Creation**: When a client requests data (e.g., `GET /api/devices/{device_id}/system/version`), instead of executing the command directly, the API creates a job and returns a job ID immediately.
2. **Job Processing**: The job is added to a queue and processed by a Celery worker.
3. **Job Status Checking**: The client can check the job status using `GET /api/tasks/{task_id}`.
4. **Results Retrieval**: When the job is completed, the client receives the actual result.

### API Flow

1. **Initial Request**: The client makes a request to an existing endpoint (e.g., `GET /api/devices/{device_id}/system/version`).
2. **Job Creation**: The backend creates a job for the command and adds it to the queue.
3. **Immediate Response**: The backend immediately responds with `{"task_id": "some-unique-id"}`.
4. **Polling**: The frontend polls the `/api/tasks/{task_id}` endpoint periodically.
5. **Result Retrieval**: When the status is `SUCCESS`, the frontend updates the UI with the received result.
6. **Error Handling**: If the status is `FAILURE`, the frontend displays an error message.

### Running the Celery Worker

To process the queued jobs, you need to run the Celery worker:

```bash
celery -A src.celery_app worker --loglevel=info
```

## Building and Running

### Prerequisites

- Python 3.12+
- PostgreSQL
- Redis

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up the environment variables:
    - Copy the `.env.sample` file to `.env`.
    - Update the `.env` file with your database credentials, Redis connection details, and a secret key for JWT.

### Running the Application

To run the application in a development environment, use the following command:

```bash
uvicorn src.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Running Tests

To run the test suite, use the following command:

```bash
pytest
```

## Interaction Policies

- **API Interaction Policy:** The user will manually start the `uvicorn` server. The agent should assume the API is running and directly proceed with API calls.

## Development Conventions

- **Coding Style:** The project follows the PEP 8 style guide for Python code.
- **TextFSM Parsing Platform:** When using TextFSM for parsing, the `platform` argument should always be the generic Netmiko device type (e.g., `cisco_ios`, `juniper_junos`), not the custom OOP device type (e.g., `cisco_ios_switch`). This ensures compatibility with `ntc-templates`.
- **Testing:** All new features should be accompanied by unit tests.
- **Branching:** Use feature branches for new development and create pull requests to merge into the main branch.
- **Commits:** Write clear and concise commit messages.
- **Repetition Policy:** If an automated process (e.g., a tool call or a sequence of actions) repeats more than 3 times without progress or a clear path forward, the process must be stopped immediately. This indicates a fundamental misunderstanding or an intractable problem with the current approach, and human intervention is required.