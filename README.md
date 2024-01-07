# FastAPI Async SQLModel Boilerplate

<p align="center">
  <a href="https://github.com/joaoflaviosantos/fastapi-async-sqlmodel-boilerplate">
    <img src="https://github-production-user-asset-6210df.s3.amazonaws.com/80658056/293617785-78ad080b-2416-473a-91cd-0adc33acf027.png" alt="White and blue rocket with FastAPI text on it. A Python logo floating next to the rocket." width="35%" height="auto">
  </a>
</p>

<p align="center">
  <a href="">
      <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  </a>
  <a href="https://fastapi.tiangolo.com">
      <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI">
  </a>
  <a href="https://sqlmodel.tiangolo.com/">
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

🚧 _Note: This project is currently under development and is a work in progress._ 🚧

This is a boilerplate project designed for building high-performance APIs using FastAPI, SQLModel (v2.0), Redis, ARQ, NGINX, and Docker. The goal is to leverage asynchronous programming as much as possible to achieve optimal performance, embracing the Django-like folder structure.

**Folder Structure Sensibility:**
The project follows a Django-like folder structure, organizing related functionalities under specific directories such as `system/auth` and `blog/posts`. This choice enhances code organization, making it intuitive for developers to locate and understand specific features. The structure aims to strike a balance between modularity and clarity.

This project aims to provide a solid foundation for developing APIs with the following cutting-edge technologies:

- **FastAPI:** A modern, fast web framework for building APIs with Python.
- **SQLModel (v2.0):** A SQL query builder and ORM for Python, incorporating SQLAlchemy 2.0, designed to reduce the mapping between persistence and transport classes. Utilizing Pydantic v2 can bring performance improvements ranging from 5x to 50x compared to Pydantic v1.
- **Redis:** In-memory data structure store, crucial for caching and other high-performance use cases. Utilized in the project through the `redis.asyncio` library for asynchronous operations. Redis is employed to create a rate limiter in conjunction with SQLModel.
- **ARQ:** A high-performance asynchronous task queue for handling asynchronous and periodic tasks. ARQ is a excelent choice for lightweight and asyncio-friendly task processing.
- **NGINX:** A high-performance web server that doubles as a reverse proxy and load balancer.
- **Docker:** Containerization for effortless deployment and scalability.

This project aims to provide a robust structure while serving as an excellent tool for quick POC validations and MVP launches. It's crafted to attract enthusiasts who appreciate how Django operates.

## Project Goals 🎯

- Leverage the power of FastAPI for building high-performance APIs.
- Use SQLModel to streamline the interaction between the database and the API.
- Implement asynchronous programming wherever applicable for optimal performance.
- Integrate Redis for caching, rate limiting, and improving data access speed.
- Utilize ARQ for handling background tasks asynchronously.
- Containerize the application with Docker for easy deployment and scalability.
- Manage database migrations seamlessly using Alembic.

🚀 **The backend for perfectionists with deadlines and enthusiasts of asynchronous programming.**

Feel free to use this boilerplate as a starting point for your own projects, and adapt it based on your specific requirements and use cases. Happy coding! 🌟

## Reference Projects 🌐

- [FastAPI Boilerplate by Igor Magalhães](https://github.com/igorbenav/FastAPI-boilerplate)
- [FastAPI Alembic SQLModel Async by Jonathan Vargas](https://github.com/jonra1993/fastapi-alembic-sqlmodel-async)
