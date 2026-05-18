# Docker Compose HTTP Example

Start the service:

```bash
docker compose up -d
```

Verify the service:

```bash
curl http://localhost:8001/health
```

Stop the service:

```bash
docker compose down
```