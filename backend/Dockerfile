FROM python:3.14-slim

# Install system dependencies required by MongoDB binaries (libgssapi, libssl) + curl for healthcheck
RUN apt-get update && \
    apt-get install -y libgssapi-krb5-2 libssl3 curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy MongoDB tools directly from the official MongoDB image
# This avoids any apt repo or CDN network issues entirely
COPY --from=mongo:7.0 /usr/bin/mongodump /usr/local/bin/
COPY --from=mongo:7.0 /usr/bin/mongorestore /usr/local/bin/
COPY --from=mongo:7.0 /usr/bin/mongoexport /usr/local/bin/
COPY --from=mongo:7.0 /usr/bin/mongoimport /usr/local/bin/
COPY --from=mongo:7.0 /usr/bin/mongosh /usr/local/bin/

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
