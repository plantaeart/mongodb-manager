FROM python:3.14-slim

# Install MongoDB tools
RUN apt-get update && \
    apt-get install -y wget gnupg curl && \
    curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
    gpg --dearmor -o /usr/share/keyrings/mongodb-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/mongodb-archive-keyring.gpg] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | \
    tee /etc/apt/sources.list.d/mongodb-org-7.0.list && \
    apt-get update && \
    apt-get install -y mongodb-org-tools mongodb-mongosh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY README.md .
COPY main.py .
COPY app/ ./app/

# Install project dependencies
RUN uv pip install --system -e .

# Create default backup directory
RUN mkdir -p /backups_mongodb_manager

# Create config and session directory (for connections.json and session.json)
RUN mkdir -p /data/.mongodb-manager && \
    chmod 755 /data/.mongodb-manager

# Set environment variable to use mounted session directory
ENV MONGODB_MANAGER_SESSION_DIR=/data/.mongodb-manager

# Expose API port
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["uvicorn", "app.main_api:app", "--host", "0.0.0.0", "--port", "8000"]
