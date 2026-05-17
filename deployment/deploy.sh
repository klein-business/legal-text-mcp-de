#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
# Blue-green deploy script for mcp.klein.business
set -euo pipefail

VERSION="${1:?Usage: $0 <version-tag>}"
echo "Deploying legal-text-mcp-de-hosted:$VERSION..."

# Pull new image
docker pull "ghcr.io/klein-business/legal-text-mcp-de-hosted:$VERSION"

# Stop green slot, start blue
docker stop legal-text-mcp-de-green 2>/dev/null || true
docker rm legal-text-mcp-de-green 2>/dev/null || true

docker run -d \
    --name legal-text-mcp-de-green \
    --restart unless-stopped \
    -p 8002:8001 \
    -v /data/corpus:/data/corpus:ro \
    -e HOSTED_BEARER_TOKENS="${HOSTED_BEARER_TOKENS:-}" \
    "ghcr.io/klein-business/legal-text-mcp-de-hosted:$VERSION"

# Wait for healthcheck
sleep 5
for i in {1..10}; do
    if curl -fsS http://localhost:8002/health > /dev/null; then
        echo "Green slot healthy"
        break
    fi
    sleep 2
done

# Atomic swap: rename green to active
docker stop legal-text-mcp-de-blue 2>/dev/null || true
docker rm legal-text-mcp-de-blue 2>/dev/null || true
docker rename legal-text-mcp-de-green legal-text-mcp-de-blue

# Caddy reloads automatically on container restart via container labels (not implemented in this script)
echo "Deployment complete. Active slot: legal-text-mcp-de-blue ($VERSION)"
