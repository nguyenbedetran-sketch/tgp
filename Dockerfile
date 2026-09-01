# Trần Gia Phát — single-image build: C++ calculator + Java report service +
# Python (Flask) backend, serving the static frontend as well.
#
# Build:  docker build -t trangia-phat .
# Run:    docker run -p 8000:8000 --env-file .env trangia-phat

FROM python:3.11-slim AS base

# --- System dependencies: g++ (C++ module), JDK (Java module) ------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        default-jdk \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Copy source ------------------------------------------------------
COPY cpp/ ./cpp/
COPY java/ ./java/
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY database/ ./database/
COPY .env.example ./.env.example

# --- Build the C++ calculation engine ----------------------------------
RUN cd cpp && g++ -std=c++17 -O2 -Wall -Wextra -o tgp_calculator main.cpp calculator.cpp

# --- Build the Java report service (no Maven Central access needed) -----
RUN cd java && chmod +x build.sh && ./build.sh

# --- Install Python dependencies ---------------------------------------
RUN pip install --no-cache-dir -r backend/requirements.txt gunicorn

# --- Runtime config ------------------------------------------------------
ENV APP_ENV=production \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    DATABASE_PATH=/app/database/tgp.db \
    UPLOAD_DIR=/app/backend/static/uploads \
    CPP_CALCULATOR_BIN=/app/cpp/tgp_calculator \
    JAVA_REPORT_JAR=/app/java/target/tgp-report-service.jar \
    LOG_DIR=/app/logs

RUN mkdir -p /app/logs /app/backend/static/uploads /app/database

EXPOSE 8000

WORKDIR /app/backend

# NOTE: SECRET_KEY must be supplied at runtime (--env-file .env or -e SECRET_KEY=...).
# The app will still boot without it (random key generated per-process) but
# every restart would invalidate existing admin sessions - do not do this in
# production.
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
