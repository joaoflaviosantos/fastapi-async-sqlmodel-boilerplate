<h1 align="center">FastAPI Async SQLModel Boilerplate</h1>

<p align="center" markdown=1>
  <i>Supercharge your FastAPI development. A backend for perfectionists with deadlines and lovers of asynchronous programming.</i>
</p>

<p align="center">
  <a href="https://github.com/joaoflaviosantos/fastapi-async-sqlmodel-boilerplate">
    <img src="https://github-production-user-asset-6210df.s3.amazonaws.com/80658056/293617785-78ad080b-2416-473a-91cd-0adc33acf027.png" alt="White and blue rocket with FastAPI text on it. A Python logo floating next to the rocket." width="35%" height="auto">
  </a>
</p>

<p align="center">
  <a href="https://www.python.org">
      <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  </a>
  <a href="https://fastapi.tiangolo.com">
      <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI">
  </a>
  <a href="https://sqlmodel.tiangolo.com">
      <img src="https://img.shields.io/badge/SQLModel-7E56C2?style=for-the-badge&logo=sqlmodel&logoColor=fff" alt="SQLModel">
  </a>
  <a href="https://docs.pydantic.dev/2.4/">
      <img src="https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=fff&style=for-the-badge" alt="Pydantic">
  </a>
  <a href="https://docs.sqlalchemy.org/en/20/">
      <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=fff" alt="SQLAlchemy">
  </a>
  <a href="https://www.postgresql.org">
      <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  </a>
  <a href="https://redis.io">
      <img src="https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=fff&style=for-the-badge" alt="Redis">
  </a>
  <a href="https://docs.docker.com/compose/">
      <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=fff&style=for-the-badge" alt="Docker">
  </a>
  <a href="https://nginx.org/en/">
      <img src="https://img.shields.io/badge/NGINX-009639?logo=nginx&logoColor=fff&style=for-the-badge" alt=NGINX>
  </a>
</p>

## 🔍 Project Overview

This **FastAPI** boilerplate for high-performance APIs leverages async programming alongside libraries such as **SQLModel**, **Redis**, **Celery**, **NGINX**, and **Docker**. It follows a Django-inspired folder structure for a clear, modular codebase. Key areas like `system/tiers`, `system/users` and `blog/posts` showcase the optimal balance between **modularity and clarity**.

It aims to provide a **robust structure** while serving as an excellent tool for quick **POC** (Proof of Concept) validations and **MVP** (Minimum Viable Product) launches. Crafted to attract enthusiasts who appreciate how Django operates, this project offers a **solid foundation** for API development, incorporating a blend of **cutting-edge technologies** and structural principles.

## 🌟 Key Features

This project seeks to provide a **strong foundation for API development**, incorporating a blend of cutting-edge technologies and structural principles:

- ⚡️ **Fully Async:** Leverage the power of asynchronous programming.
- 🚀 **FastAPI:** Utilize FastAPI for rapid API development.
- 🧰 **SQLModel:** Seamlessly integrates with SQLAlchemy 2.0 for versatile Python SQL operations, reducing the mapping between persistence and transport classes. Using Pydantic v2 can result in performance improvements from 5x to 50x compared to Pydantic v1.
- 🔐 **JWT User Authentication:** Secure user authentication using JSON Web Tokens.
- 🍪 **Cookie-based Refresh Token:** Implement a refresh token mechanism using cookies.
- 🏬 **Easy Redis Caching:** Utilize Redis for simple and effective caching.
- 👜 **Client-side Caching:** Facilitate easy client-side caching for improved performance.
- 🚦 **Celery Integration:** Seamlessly integrate Celery for distributed task queue management with async task support, scheduled jobs via Celery Beat, and PostgreSQL result backend.
- ⚙️ **Efficient Querying:** Optimize database queries by fetching only what's needed, with support for joins.
- ⎘ **Pagination Support:** Out-of-the-box pagination support for enhanced data presentation.
- 🛑 **Rate Limiter Dependency:** Implement a rate limiter for controlled API access.
- 👮 **Secure FastAPI Docs:** Restrict FastAPI docs behind authentication and hide based on the environment.
- 🦾 **Easily Extendable:** Extend and customize the project effortlessly.
- 🤸‍♂️ **Flexible:** Adapt the boilerplate to suit your specific needs.
- 🚚 **Docker Compose:** Easily run the project with Docker Compose.
- ⚖️ **NGINX Reverse Proxy and Load Balancing:** Enhance scalability with NGINX reverse proxy and load balancing.

## 🎯 Project Goals

- [x] Leverage the power of FastAPI for building high-performance APIs.
- [x] Implement asynchronous programming wherever applicable for optimal performance.
- [x] Integrate Redis for caching, rate limiting, and improving data access speed.
- [x] Utilize Celery for handling background tasks asynchronously with full async/await support.
- [x] Implement a robust logging system to track and manage application events efficiently.
- [x] Manage database migrations seamlessly using Alembic.
- [x] Develop comprehensive unit tests for API endpoints using pytest.
- [x] Implement using SQLModel to streamline the interaction between the database and the API.
- [ ] Provide a CLI tool for easy project execution and management.
- [ ] Provide diverse deployment options to ensure flexibility and accessibility.

## 📋 Prerequisites

Before you begin, ensure you have the following prerequisites installed and configured:

- [PostgreSQL](https://www.postgresql.org): Set up a PostgreSQL database.
- [Redis](https://redis.io): Install and configure a Redis server.
- [Python](https://www.python.org): Make sure to have Python 3.11 or a newer version installed on your system.
- [Poetry](https://python-poetry.org): Install Poetry for managing dependencies.

### Installing Poetry

Poetry is a dependency manager for Python. Follow the steps below to install Poetry **version 1.7.1** (required):

1. Open a terminal.

2. Run the following command to install Poetry using pip:

   ```bash
   pip install poetry==1.7.1
   ```

3. Verify the installation by running:

   ```bash
   poetry --version
   ```

   This should display `Poetry (version 1.7.1)`. If you have a different version installed, please uninstall and reinstall the correct version:

   ```bash
   pip uninstall poetry
   pip install poetry==1.7.1
   ```

### Using Docker Compose (Alternative Setup)

If you prefer to use Docker containers for development, you can easily set up PostgreSQL and Redis using Docker Compose:

1. Ensure you have [Docker](https://www.docker.com) and [Docker Compose](https://docs.docker.com/compose/) installed on your system.

2. From the **root directory** of the project, run the following command to start PostgreSQL and Redis containers:

   ```bash
   docker compose --env-file backend/.env -f docker/docker-compose.yml --project-name fastapi-async-sqlmodel-boilerplate up -d
   ```

   This command will:
   - Load environment variables from `backend/.env`
   - Use the Docker Compose configuration from `docker/docker-compose.yml`
   - Start PostgreSQL and Redis containers in detached mode
   - Create necessary volumes for data persistence

3. Verify the services are running:

   ```bash
   docker compose --project-name fastapi-async-sqlmodel-boilerplate ps
   ```

4. To stop the services:

   ```bash
   docker compose --project-name fastapi-async-sqlmodel-boilerplate down
   ```

**Note:** The command uses environment variables from `backend/.env`, so ensure that file is properly configured before running the containers.

Now that the prerequisites are met, you can begin working on your project. Choose either the manual setup or Docker Compose based on your preference.

## 🤖 Running the Project CLI

To streamline the usage of this boilerplate, we've provided a convenient **CLI tool**. From the **root project directory**, execute the following steps:

1. Clone the repository, running the following command:

```bash
git clone https://github.com/joaoflaviosantos/fastapi-async-sqlmodel-boilerplate.git
```

2. Navigate to the cloned repository:

```bash
cd fastapi-async-sqlmodel-boilerplate
```

3. Run the setup (**CLI tool**) command:

```bash
python3 setup.py
```

This command automates various **setup tasks**, making it easier to **get started** with the project.

For more details for a manual setup, please refer to the [Backend README](backend/README.md) section.

## 🌐 Reference Projects

- [FastAPI Boilerplate by Igor Magalhães](https://github.com/igorbenav/FastAPI-boilerplate)
- [FastAPI Alembic SQLModel Async by Jonathan Vargas](https://github.com/jonra1993/fastapi-alembic-sqlmodel-async)

Feel free to use this boilerplate as a starting point for your own projects, and adapt it based on your specific requirements and use cases. Happy coding! 🌟
