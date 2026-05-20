# Demo Script

1. Start stack:

```bash
docker compose up --build -d
```

2. Check health:

```bash
curl http://localhost:8500/services/health
```

3. Trigger workflow:

```bash
curl -X POST http://localhost:8500/workflow/log-workout \
  -H "Content-Type: application/json" \
  -d '{"user_id":"USR-DEMO","activity_type":"functional","duration_minutes":50,"distance_km":0.0,"weight_kg":78}'
```

4. Open dashboard:

```bash
curl http://localhost:8500/dashboard/USR-DEMO
```
