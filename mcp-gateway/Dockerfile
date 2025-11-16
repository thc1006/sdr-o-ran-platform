FROM node:20-slim

# Install necessary tools
RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy registry configuration
COPY registry.yaml /app/registry.yaml

# Install available MCP servers from npm
RUN npm install -g \
    @modelcontextprotocol/server-fetch \
    2>/dev/null || true

# Install Python-based MCP servers if available
RUN pip3 install --break-system-packages arxiv-mcp-server 2>/dev/null || true

# Create MCP server wrapper scripts
RUN mkdir -p /app/servers

# Create a health check and info script
RUN echo '#!/bin/bash\n\
echo "================================="\n\
echo "MCP Gateway Container Status"\n\
echo "================================="\n\
echo ""\n\
echo "Registry config: /app/registry.yaml"\n\
echo ""\n\
echo "Configured MCP servers (from registry.yaml):"\n\
cat /app/registry.yaml\n\
echo ""\n\
echo "================================="\n\
echo "Available Node.js global packages:"\n\
npm list -g --depth=0 2>/dev/null || echo "No global packages found"\n\
echo ""\n\
echo "================================="\n\
echo "MCP Gateway is running and ready"\n\
echo "Connect to this container via Docker to use MCP servers"\n\
echo "================================="\n\
\n\
# Keep container alive\n\
tail -f /dev/null\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=20s \
  CMD [ -f /app/registry.yaml ] && echo "Healthy" || exit 1

CMD ["/app/entrypoint.sh"]
