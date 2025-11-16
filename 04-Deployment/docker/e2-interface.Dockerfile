FROM python:3.12-slim

LABEL maintainer="SDR-O-RAN Team <sdr-oran@example.com>"
LABEL description="E2 Interface for Near-RT RIC"
LABEL version="1.0.0"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    libsctp-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy E2 Interface code
COPY 03-Implementation/ric-platform/e2-interface/ /app/e2-interface/

# Set Python path
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Create non-root user
RUN useradd -m -u 1000 e2user && \
    chown -R e2user:e2user /app
USER e2user

# Expose ports
EXPOSE 36421/sctp
EXPOSE 8080/tcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run E2 Interface
CMD ["python", "-m", "e2-interface.e2_manager"]
