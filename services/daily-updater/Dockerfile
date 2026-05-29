FROM --platform=linux/arm64 python:3.12-slim
WORKDIR /app

# py-lets-be-rational (dep of py_vollib_vectorized) has no arm64 wheel and
# builds from source; needs gcc + Python headers.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY daily_updater.py .
CMD ["python", "daily_updater.py"]
