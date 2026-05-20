# Deployment Guide

## Local docker start

```bash
docker compose up --build -d
```

## Environment variables

Core variables are in `.env.example`:

- service ports (`8500..8507`)
- PostgreSQL DSN
- MongoDB URI
- RabbitMQ URL
- Redis URL
- gateway service URLs

## Health checks

- `GET http://localhost:8500/health`
- `GET http://localhost:8500/services/health`

## Scale hints

- scale `tracking-service` and `analytics-service` first
- keep MongoDB on separate volume
- split analytics by user shards (`/analytics/sharding-plan`)
