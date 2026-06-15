# Image for both the monitor (bot) and the web UI -- same code, different
# command in docker-compose. The IB Gateway itself runs in a separate image
# (gnzsnz/ib-gateway); this container only speaks the API over the network.
FROM python:3.13-slim

WORKDIR /app

# PYTHONUNBUFFERED so logs stream to `docker compose logs` in real time
# (the block-buffering we hit running the monitor backgrounded locally).
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py watchlist_phb.txt ./

# Overridden per-service in docker-compose.yml.
CMD ["python", "signal_monitor.py", "--help"]
