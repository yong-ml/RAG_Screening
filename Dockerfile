FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml .

# Install dependencies
# --system installs into the system python environment, avoiding venv creation inside container
RUN uv pip install --system -r pyproject.toml

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Command
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
