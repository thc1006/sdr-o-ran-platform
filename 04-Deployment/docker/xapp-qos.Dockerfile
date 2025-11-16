FROM python:3.12-slim

LABEL maintainer="SDR-O-RAN Team <sdr-oran@example.com>"
LABEL description="QoS Optimizer xApp"
LABEL version="1.0.0"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy xApp SDK and QoS xApp code
COPY 03-Implementation/ric-platform/xapp-sdk/ /app/xapp-sdk/
COPY 03-Implementation/ric-platform/xapps/qos_optimizer_xapp.py /app/xapps/
COPY 03-Implementation/ric-platform/e2-interface/ /app/e2-interface/

# Set Python path
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Create non-root user
RUN useradd -m -u 1000 xappuser && \
    chown -R xappuser:xappuser /app
USER xappuser

# Expose HTTP port
EXPOSE 8000/tcp

# Health check
HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run QoS xApp
CMD ["python", "-m", "xapps.qos_optimizer_xapp"]
