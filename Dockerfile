# Stage 1: Builder
FROM python:3.11-alpine AS builder

WORKDIR /app

# Pasang build dependencies & poetry
RUN apk add --no-cache build-base libffi-dev openssl-dev \
    && pip install poetry \
    && poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true \
    && poetry config cache-dir /opt/poetry

# Salin file konfigurasi
COPY pyproject.toml poetry.lock* ./

# Instal dependensi ke direktori spesifik
RUN poetry install --no-root && \
    rm -rf ~/.cache/pypoetry ~/.cache/pip


# Stage 2: Runtime
FROM python:3.11-alpine

WORKDIR /app

# Salin virtual environment dan kode sumber
COPY --from=builder /app/.venv /app/.venv
COPY src/ src/

# Set PATH agar bisa menjangkau uvicorn di virtualenv
ENV PATH="/app/.venv/bin:$PATH"

# Tambahkan user non-root
RUN adduser --disabled-password --gecos '' arosyihuddin

# Ekspos port aplikasi
EXPOSE 8000

# Jalankan aplikasi sebagai user non-root
USER arosyihuddin
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]
