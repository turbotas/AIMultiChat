# Stage 1: Build Stage
FROM python:3.12-alpine AS builder

# Install build dependencies temporarily
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    && pip install --no-cache-dir gunicorn gevent gevent-websocket

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final Image (Minimal Size)
FROM python:3.12-alpine

WORKDIR /app

# Copy only the necessary app files
COPY . .

# Copy pre-built dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn

# Expose the correct port
EXPOSE 5000

# Final command
CMD ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]
