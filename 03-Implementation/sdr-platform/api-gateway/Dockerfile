# Multi-stage Dockerfile for SDR API Gateway
# Optimized for cloud-native deployment (FR-SDR-004)

# =============================================================================
# Stage 1: Build stage (optional, for future C++ extensions)
# =============================================================================
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# =============================================================================
# Stage 2: Runtime stage
# =============================================================================
FROM python:3.11-slim

# Metadata labels
LABEL maintainer="thc1006@ieee.org"
LABEL version="1.0.0"
LABEL description="SDR Ground Station API Gateway for O-RAN Integration"

# Create non-root user for security (NFR-SEC-001)
RUN useradd -m -u 1000 sdruser

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/sdruser/.local

# Copy application code
COPY sdr_api_server.py .

# Set ownership
RUN chown -R sdruser:sdruser /app

# Switch to non-root user
USER sdruser

# Add local Python packages to PATH
ENV PATH=/home/sdruser/.local/bin:$PATH

# Expose API port
EXPOSE 8080

# Health check (FR-SDR-004)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/healthz')" || exit 1

# Run application
CMD ["python", "sdr_api_server.py"]

# =============================================================================
# Build Instructions:
# =============================================================================
# docker build -t sdr-api-gateway:1.0.0 .
# docker run -p 8080:8080 sdr-api-gateway:1.0.0
#
# Kubernetes Deployment:
# kubectl apply -f ../../../04-Deployment/kubernetes/sdr-api-gateway.yaml
