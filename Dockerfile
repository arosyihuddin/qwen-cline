# Stage 1: Builder
FROM python:3.11-slim-buster AS builder

WORKDIR /app

# Install Poetry tanpa cache
RUN pip install poetry && \
    poetry config virtualenvs.create true && \
    poetry config virtualenvs.in-project true && \
    poetry config cache-dir /opt/poetry
VOLUME /opt/poetry

# Salin file konfigurasi
COPY pyproject.toml poetry.lock* ./

# Instal dependensi ke direktori spesifik
RUN poetry install --no-root

# Stage 2: Runtime
FROM python:3.11-slim-buster

WORKDIR /app

# Salin virtual environment dan kode sumber
COPY --from=builder /app/.venv /app/.venv
COPY src/ src/

# Set PATH agar bisa menjangkau uvicorn di virtualenv
ENV PATH="/app/.venv/bin:$PATH"

# Install tool tambahan (sebagai root)
RUN apt-get update && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Tambahkan user non-root
RUN adduser --disabled-password --gecos '' arosyihuddin

# Ekspos port aplikasi
EXPOSE 8000

# Jalankan aplikasi sebagai user non-root
USER arosyihuddin
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]
