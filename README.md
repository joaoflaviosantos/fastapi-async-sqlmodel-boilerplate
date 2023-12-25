# FastAPI SQLModel Async Boilerplate 🚀

🚧 _Note: This project is currently under development and is a work in progress._ 🚧

This is a boilerplate project designed for building high-performance APIs using FastAPI, SQLModel (v2.0), Redis, Celery, NGINX, and Docker. The goal is to leverage asynchronous programming as much as possible to achieve optimal performance, embracing the Django-like folder structure.

This project aims to provide a solid foundation for developing APIs with the following cutting-edge technologies:

- **FastAPI:** A modern, fast web framework for building APIs with Python.
- **SQLModel (v2.0):** A SQL query builder and ORM for Python, incorporating SQLAlchemy 2.0, designed to reduce the mapping between persistence and transport classes. Utilizing Pydantic v2 can bring performance improvements ranging from 5x to 50x compared to Pydantic v1.
- **Redis:** In-memory data structure store, crucial for caching and other high-performance use cases. Utilized for creating a rate limiter in conjunction with SQLModel.
- **Celery:** A distributed task queue for handling asynchronous and periodic tasks.
- **NGINX:** A high-performance web server that doubles as a reverse proxy and load balancer.
- **Docker:** Containerization for effortless deployment and scalability.

This project aims to provide a robust structure while serving as an excellent tool for quick POC validations and MVP launches. It's crafted to attract enthusiasts who appreciate how Django operates.

## Project Goals 🎯

- Leverage the power of FastAPI for building high-performance APIs.
- Use SQLModel to streamline the interaction between the database and the API.
- Implement asynchronous programming wherever applicable for optimal performance.
- Integrate Redis for caching, rate limiting, and improving data access speed.
- Utilize Celery for handling background tasks asynchronously.
- Containerize the application with Docker for easy deployment and scalability.
- Manage database migrations seamlessly using Alembic.

🚀 **The backend for perfectionists with deadlines and enthusiasts of asynchronous programming.**

Feel free to use this boilerplate as a starting point for your own projects, and adapt it based on your specific requirements and use cases. Happy coding! 🌟

## Reference Projects 🌐

- [FastAPI Boilerplate by Igor Magalhães](https://github.com/igorbenav/FastAPI-boilerplate)
- [FastAPI Alembic SQLModel Async by Jonathan Vargas](https://github.com/jonra1993/fastapi-alembic-sqlmodel-async)
