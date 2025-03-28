FROM python:3.12 AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-editable --only-group alembic

# Copy the project into the intermediate image
ADD . /app

# Install the project package
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --no-deps .

FROM python:3.12-slim

# Copy the environment and source code
COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

WORKDIR /app

# Run the application
CMD ["alembic", "upgrade", "head"]
