# Multi-Currency Ledger API

A backend REST API that simulates a simple multi-currency ledger system inspired by modern fintech platforms. The project allows users to create accounts, track balances, and perform transfers while ensuring accurate ledger records. It is built with FastAPI, PostgreSQL, SQLAlchemy, Docker, and tested using Pytest.

---

## Features

- Create ledger accounts
- Retrieve account balances
- Transfer funds between accounts
- PostgreSQL database integration
- SQLAlchemy ORM
- RESTful API with FastAPI
- Dockerized deployment
- Automated testing with Pytest
- Kubernetes deployment configuration

---

# System Architecture

![Architecture](image/architecture.png)

---

# API Documentation

Interactive API documentation is automatically generated with Swagger UI.

![Swagger UI](image/swagger-UI.png)

---

## Live Demo

Once the application is running locally with Docker Compose, the API documentation is available at:

http://localhost:8000/docs

This interactive Swagger UI allows users to:

- Create accounts
- View balances
- Transfer funds
- Test every endpoint directly from the browser

> **Note:** This project currently runs locally. Cloud deployment (GCP) is planned as a future improvement.

# Docker Deployment

The application and PostgreSQL database run together using Docker Compose.

![Docker Running](image/docker-running.png)

---

# Automated Testing

All API functionality is verified using Pytest.

**Current Status:** **11 tests passed**

![Tests Passing](image/Tests%20passing.png)

---

# Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.12 | Backend programming language |
| FastAPI | REST API framework |
| SQLAlchemy | ORM |
| PostgreSQL | Database |
| Docker | Containerization |
| Docker Compose | Multi-container deployment |
| Pytest | Automated testing |
| Kubernetes | Deployment configuration |

---

# Project Structure

```text
revolut-fraud-pipeline/
│
├── app/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   └── ...
│
├── tests/
│
├── image/
│   ├── architecture.png
│   ├── swagger-UI.png
│   ├── docker-running.png
│   └── Tests passing.png
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── kubernetes.yaml
└── README.md
```

---

# Installation

Clone the repository

```bash
git clone https://github.com/safaribenitha/ledger-api.git
```

Navigate into the project

```bash
cd ledger-api
```

Build and start the containers

```bash
docker compose up --build
```

Open the API documentation

```
http://localhost:8000/docs
```

---

# API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/accounts` | Create a new account |
| GET | `/accounts/{account_id}/balance` | Get account balance |
| GET | `/balance` | Read balances |
| POST | `/transfers` | Transfer funds |

---

# Running Tests

```bash
pytest
```

Expected output

```
11 passed
```

---

# Future Improvements

- Kafka event streaming
- Apache Airflow workflow orchestration
- Google Cloud deployment
- Authentication & Authorization
- Monitoring and logging
- CI/CD pipeline with GitHub Actions

---

# Author

**Safari Umutesi Benitha**

Backend Developer | Automation & Robotics Student

GitHub: https://github.com/safaribenitha