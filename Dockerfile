# Use official Python lightweight image
FROM python:3.12-slim as builder

WORKDIR /app

# Install compilation dependencies for TgCrypto (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies to a local directory to keep image clean
RUN pip install --no-cache-dir --user -r requirements.txt

# Final minimal image
FROM python:3.12-slim

WORKDIR /app

# Copy installed libraries from the builder stage
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Koyeb uses PORT 8000 by default
EXPOSE 8000

CMD ["python", "bot.py"]
