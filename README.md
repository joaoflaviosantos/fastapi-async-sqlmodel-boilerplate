# FastAPI SQLModel Async Boilerplate

This is a boilerplate project designed for building high-performance APIs using FastAPI, SQLModel, Redis, Celery, NGINX, and Docker. The goal is to leverage asynchronous programming as much as possible to achieve optimal performance.

## Project Overview

This boilerplate is designed to provide a foundation for building APIs with the following technologies:

- **FastAPI:** A modern, fast web framework for building APIs with Python.
- **SQLModel:** A SQL query builder and ORM for Python, designed to reduce the mapping between persistence and transport classes.
- **Redis:** In-memory data structure store, useful for caching and other high-performance use cases. Utilized for creating a rate limiter in conjunction with SQLModel.
- **Celery:** A distributed task queue for handling asynchronous and periodic tasks.
- **NGINX:** A high-performance web server that can also act as a reverse proxy and load balancer.
- **Docker:** Containerization for easy deployment and scalability.

## Project Goals

- Leverage the power of FastAPI for building high-performance APIs.
- Use SQLModel to streamline the interaction between the database and the API.
- Implement asynchronous programming wherever applicable for optimal performance.
- Integrate Redis for caching, rate limiting, and improving data access speed.
- Utilize Celery for handling background tasks asynchronously.
- Containerize the application with Docker for easy deployment and scalability.
- Manage database migrations seamlessly using Alembic.

## Project Structure

```sh
.
├── LICENSE
├── README.md
└── src
    ├── __init__.py
    ├── __pycache__
    │   └── main.cpython-311.pyc
    ├── alembic
    │   ├── README
    │   ├── __init__.py
    │   ├── alembic.ini
    │   ├── env.py
    │   ├── script.py.mako
    │   └── versions
    ├── apps
    │   ├── __init__.py
    │   ├── system
    │   │   ├── __init__.py
    │   │   ├── authentication
    │   │   │   ├── __init__.py
    │   │   │   ├── crud.py
    │   │   │   ├── deps.py
    │   │   │   ├── exceptions.py
    │   │   │   ├── models.py
    │   │   │   ├── routers
    │   │   │   │   ├── __init__.py
    │   │   │   │   └── v1.py
    │   │   │   └── schemas.py
    │   │   ├── companies
    │   │   │   ├── __init__.py
    │   │   │   ├── crud.py
    │   │   │   ├── deps.py
    │   │   │   ├── exceptions.py
    │   │   │   ├── models.py
    │   │   │   ├── routers
    │   │   │   │   ├── __init__.py
    │   │   │   │   └── v1.py
    │   │   │   └── schemas.py
    │   │   └── users
    │   │       ├── __init__.py
    │   │       ├── crud.py
    │   │       ├── deps.py
    │   │       ├── exceptions.py
    │   │       ├── models.py
    │   │       ├── routers
    │   │       │   ├── __init__.py
    │   │       │   └── v1.py
    │   │       └── schemas.py
    │   └── tasks
    │       ├── __init__.py
    │       ├── crud.py
    │       ├── exceptions.py
    │       ├── routers
    │       │   ├── __init__.py
    │       │   └── v1.py
    │       └── schemas.py
    ├── core
    │   ├── __init__.py
    │   ├── __pycache__
    │   │   ├── __init__.cpython-311.pyc
    │   │   └── config.cpython-311.pyc
    │   ├── api
    │   │   ├── __init__.py
    │   │   └── v1.py
    │   ├── common
    │   │   ├── __init__.py
    │   │   ├── crud.py
    │   │   ├── deps.py
    │   │   ├── exceptions.py
    │   │   ├── models.py
    │   │   ├── schemas
    │   │   │   ├── __init__.py
    │   │   │   └── response_schema.py
    │   │   └── security.py
    │   ├── config.py
    │   ├── db
    │   │   ├── __init__.py
    │   │   ├── init_db.py
    │   │   └── session.py
    │   ├── middlewares
    │   │   ├── __init__.py
    │   │   ├── __pycache__
    │   │   │   ├── __init__.cpython-311.pyc
    │   │   │   └── fastapi_globals.cpython-311.pyc
    │   │   └── fastapi_globals.py
    │   └── security.py
    ├── docs
    ├── main.py
    ├── poetry.lock
    ├── poetry.toml
    ├── pyproject.toml
    ├── tests
    │   └── __init__.py
    └── utils
        ├── __init__.py
        ├── redis.py
        ├── scripts
        │   ├── __init__.py
        │   └── database
        │       ├── __init__.py
        │       └── initial_data_script.py
        └── uuid6.py
```

Feel free to use this boilerplate as a starting point for your own projects, and adapt it based on your specific requirements and use cases. Happy coding!
