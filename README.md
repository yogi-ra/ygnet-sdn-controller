### 1. Introduction

This document outlines the architecture and features of this SDN Controller, a Python-based Software-Defined Networking (SDN) controller. Built using the modern FastAPI framework, it provides a centralized, programmatic interface for managing and interacting with a diverse range of network devices.

The system is designed to be asynchronous, scalable, and resilient, leveraging a RESTful API to expose its functionalities. Key features include a robust connection management system for handling device interactions, role-based access control for security, and a Celery-based task queue for asynchronous network operations. This controller serves as a foundational platform for automating network operations and enabling advanced network services.

### 2. Project Background

In modern networking, the ability to automate and dynamically control the network fabric is crucial for security and operational efficiency. The YgNet SDN Controller was developed to provide this control by abstracting the underlying complexity of individual network devices into a unified API.

The primary driver for this project is to serve as the core engine for a Network Access Control (NAC) solution. A NAC system requires the ability to dynamically identify, authenticate, authorize, and monitor devices as they connect to a network. This SDN API provides the essential building blocks for such a system. For example, a NAC application could leverage this API for:

* **Dynamic VLAN Assignment**: Moving a device to a specific network segment (e.g., a "quarantine" VLAN for non-compliant devices or a "guest" VLAN for visitors) based on its identity and security posture.

By providing a stable and secure API, this project enables the development of these and other value-added services without needing to interact directly with the network hardware.

### 3. Development Objectives

The development of the SDN controller is guided by the following key objectives:

* **Centralized Management**: To create a single point of control for managing a heterogeneous network of devices from different vendors (e.g., Cisco, Aruba, Ubiquiti).
* **Asynchronous Operations**: To ensure the API remains responsive by offloading long-running network tasks to background workers.
* **Scalability**: To design a system that can manage a growing number of devices without performance degradation.
* **Security**: To implement robust authentication and authorization mechanisms to protect network infrastructure.
* **Extensibility**: To create a modular architecture that allows for easy addition of new device types and features.

## 4. Technology Stack
* **Backend Framework**: FastAPI
* **Frontend Framework**: React with TypeScript
* **Asynchronous Task Queuing**: Celery
* **Database ORM**: PostgreSQL, SQLite (fallback)
* **Network Automation**: Netmiko
* **Message Broker & Cache**: Redis
* **Authentication**: JWT
* **Configuration**: `pydantic-settings`
* **Testing**: Pytest

## 5. Architectural Pattern
The application is structured using a classic Three-Tier Architecture, which provides a clear and robust separation of concerns.

* **Tier 1: Presentation Tier (API Layer)**: This is the FastAPI layer that exposes RESTful endpoints to the client. It handles HTTP requests, validation using Pydantic, and authentication.
* **Tier 2: Business Logic Tier (Application Layer)**: This layer contains the core application logic, including device controllers, and services that orchestrate network operations.
* **Tier 3: Data Tier (Persistence Layer)**: This tier consists of the PostgreSQL database, managed via SQLAlchemy ORM, for storing device inventory, user data, and configuration.

### Project Structure
The project is composed of several key modules that work together:

- **`main.py`**: The FastAPI application entrypoint. Initializes the app, and includes the API routers.
- **`src/database.py`**: Handles database connection and session management.
- **`src/models.py`**: Defines the SQLAlchemy database models.
- **`src/schemas.py`**: Defines the Pydantic schemas for data validation and serialization.
- **`src/crud.py`**: Contains the core database CRUD (Create, Read, Update, Delete) logic.
- **`src/controllers/`**: Contains vendor-specific device controllers that encapsulate device interaction logic.
- **`src/api/`**: Contains the FastAPI routers and endpoints.
- **`src/security.py`**: Implements authentication, authorization, and password hashing.
- **`src/config.py`**: Manages application settings and environment variables using Pydantic.
- **`src/celery_app.py`**: Defines and configures the Celery application instance.
- **`src/tasks.py`**: Contains the Celery tasks for executing asynchronous device commands.

## 6. Asynchronous Architecture & Concurrency Model

The system employs a hybrid concurrency model to maximize performance. The FastAPI web layer operates on an `asyncio` event loop, making it highly efficient for handling I/O-bound tasks like waiting for HTTP requests.

However, the `netmiko` library used for network automation is synchronous (blocking). A naive integration would cause these blocking network calls to freeze the entire application. To solve this, all blocking `netmiko` operations are offloaded to a Celery distributed task queue, which runs in separate worker processes.

### How It Works

1.  **Job Creation**: When a client requests a long-running operation (e.g., `GET /api/devices/{device_id}/system/version`), the API creates a Celery task and returns a `task_id` to the client immediately.
2.  **Job Processing**: The task is added to a Redis queue. A dedicated Celery worker picks up the task and executes the blocking `netmiko` command.
3.  **Status Polling**: The client application (frontend) polls the `/api/tasks/{task_id}` endpoint to check the status of the job (`PENDING`, `SUCCESS`, or `FAILURE`).
4.  **Results Retrieval**: Once the job status is `SUCCESS`, the response from the task endpoint contains the actual result of the network command. The client can then display the data.

This design is crucial for achieving both high responsiveness in the API and efficient, non-blocking network automation at scale.

## 7. Supported Device Types

- **Cisco IOS Router** (`cisco_ios_router`): For Cisco routers running IOS.
- **Cisco IOS Switch** (`cisco_ios_switch`): For Cisco switches running IOS.

## 8. Building and Running

### Prerequisites

- Python 3.12+
- PostgreSQL
- Redis

### Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate
    # On Windows, use: .\venv\Scripts\activate
    ```

3.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Set up the environment variables:
    - Copy the `.env.sample` file to `.env`.
    - Update the `.env` file with your database credentials, Redis connection details, and a secret key for JWT.

### Running the Application

1.  **Start the API Server**:
    To run the application in a development environment, use `uvicorn`:
    ```bash
    uvicorn src.main:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`.

2.  **Start the Celery Worker**:
    To process the asynchronous jobs, you must run at least one Celery worker in a separate terminal:
    ```bash
    celery -A src.celery_app worker --concurrency 5 --loglevel=info
    ```

## 9. Running Tests

To run the test suite, use `pytest`:

```bash
pytest
```

## 10. Development Conventions

- **Coding Style**: The project follows the PEP 8 style guide for Python code.
- **TextFSM Parsing Platform**: When using TextFSM for parsing, the `platform` argument should always be the generic Netmiko device type (e.g., `cisco_ios`), not the custom OOP device type (e.g., `cisco_ios_switch`). This ensures compatibility with `ntc-templates`.
- **Testing**: All new features should be accompanied by unit tests.
- **Branching**: Use feature branches for new development and create pull requests to merge into the main branch.
- **Commits**: Write clear and concise commit messages.
- **Repetition Policy**: If an automated process (e.g., a tool call or a sequence of actions) repeats more than 3 times without progress or a clear path forward, a process must be stopped immediately. This indicates a fundamental misunderstanding or an intractable problem with the current approach, and human intervention is required.
