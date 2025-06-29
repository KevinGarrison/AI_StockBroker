# 255-cd-teamB Project

## Overview

This is a comprehensive cloud-native application built by Team B for the Cloud Distributed Computing course at Aalen University 2025. It includes multiple backend microservices, a React frontend, monitoring and logging tools (Grafana + Fluent Bit), time-series storage with InfluxDB, and containerized deployment with Docker Compose.

## Clean Code & Architecture Principles

This project adheres to industry best practices to ensure high code quality, maintainability, and scalability.

### SOLID Principles

We apply the SOLID design principles across all microservices:

- **S** – *Single Responsibility Principle*: Each module or function has one clear responsibility.
- **O** – *Open/Closed Principle*: Components are open for extension, but closed for modification.
- **L** – *Liskov Substitution Principle*: Services are designed to be substitutable without breaking behavior.
- **I** – *Interface Segregation Principle*: Interfaces are client-specific and not bloated.
- **D** – *Dependency Inversion Principle*: High-level modules do not depend on low-level modules. Abstractions are key.

### Clean Architecture

We follow Clean Architecture concepts:

- **Separation of Concerns**: Logic is decoupled from frameworks and I/O.
- **Domain-Centric**: Business logic drives the structure.
- **Independent Layers**: Each layer (e.g. routing, services, data) is isolated and testable.
- **Port & Adapter Model**: Allows easy swap of databases, APIs, or external tools.

### CP88 Compliance

This project meets the expectations of the **CP88 Clean Code & Microservice Architecture** unit by demonstrating:

- Modular service boundaries
- Configuration via `.env` and Docker Compose
- Infrastructure-as-code principles
- Observability (logging + monitoring)
- Robust naming conventions and documentation

## Project Architecture

```
.
├── backend/microservices/
│   ├── api_fetcher/
│   ├── api_gateway/
│   ├── forecasting/
│   ├── influx/
│   └── rag_chatbot/
├── frontend/
│   ├── public/
│   ├── src/
│   ├── Dockerfile
│   ├── package.json
│   └── README.md
├── grafana/
│   ├── grafana.ini
│   ├── History/
│   ├── History & Forecast/
│   └── Logs/
├── nginx/
│   └── nginx.conf
├── notebooks/
├── fluent-bit/
│   ├── fluent-bit.conf
│   ├── parsers.conf
│   ├── enrich_docker_log.lua
│   └── extract_container_name.lua
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── .env.example
└── README.md
```

---

## Tech Stack

- **Frontend**: React
- **Backend**: Python (Microservices)
- **Database**: InfluxDB (time-series), Redis, Qdrant (vector DB)
- **Monitoring**: Grafana
- **Logging**: Fluent Bit
- **Deployment**: Docker, Docker Compose, Nginx

---

## Getting Started

### 1. Environment Setup

Copy and configure your environment file:

```bash
cp .env.example .env
```

Update values in `.env` including:

```env
DOCKER_INFLUXDB_INIT_USERNAME=admin
DOCKER_INFLUXDB_INIT_PASSWORD=adminadmin
DOCKER_INFLUXDB_INIT_ORG=HSAA
DOCKER_INFLUXDB_INIT_BUCKET=25s-cd-teamb
DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=mySuperSecretToken123!
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=adminadmin
USER_AGENT_SEC=your-secret
DEEPSEEK_API_KEY=your-api-key
OPENAI_API_KEY=your-api-key
QDRANT_HOST=qdrant
QDRANT_PORT=6333
COLLECTION_NAME=your-vector-collection
REDIS_HOST=redis
```

---

### 2. Install Python 3.12 (if needed)

#### Ubuntu/Debian

```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.12 -y
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
```

#### macOS (Homebrew)

```bash
brew update
brew install python@3.12
brew link --overwrite python@3.12
```

#### Windows

1. Download from: https://www.python.org/downloads/release/python-3120/
2. Run installer and check *Add Python to PATH*
3. Confirm:

```powershell
python --version
```

---

### 3. Start the Application

#### Development

```bash
docker-compose -f docker-compose.dev.yml up --build
```

#### Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## Services

### Databases

- **InfluxDB**: Time-series database for metrics
- **Redis**: In-memory cache/database
- **Qdrant**: Vector search database

### Microservices (Backend)

- **api-gateway**: Orchestrates backend communication
- **api-fetcher**: Fetches and processes external data
- **forecasting**: Forecast logic (likely ML-based)
- **influx-client**: Interfaces with InfluxDB
- **rag-chatbot**: RAG-based assistant using vector search + LLM

### Frontend

- **frontend**: React UI
- **nginx**: Reverse proxy for frontend/backend routes

### Observability

- **grafana**: Metrics dashboards
- **fluent-bit**: Log aggregation, parsing, enrichment

### Optional

- **redisinsight**: GUI for Redis (http://localhost:5540)

---

## Access Points

| Service        | URL                        |
|----------------|----------------------------|
| Frontend       | http://localhost           |
| Grafana        | http://localhost:3000      |
| RedisInsight   | http://localhost:5540      |
| InfluxDB       | http://localhost:8086      |

---

## Volumes

These are declared in `docker-compose`:

- `influxdb-data`
- `grafana-data`
- `qdrant-data`
- `redis-data`
- `redisinsight-data`

---

## Testing & Debugging

- Use `docker logs <container>` for troubleshooting
- Use `docker-compose ps` to check service health
- Test API endpoints through `nginx` exposed at port `80`

---

## License

MIT License — Team B, 255-CD Cohort

---

## Support
* Repo owners:  kevin.garrison@studmail.htw-aalen.de, ilef.kalboussi@studmail.htw-aalen.de, pardis.ebrahimi@studmail.htw-aalen.de, lukas.hauser@studmail.htw-aalen.de
If you encounter issues, check the logs of failing services or validate environment variables are correctly configured.
