# FitLife

FitLife is an online personal fitness trainer platform with personalized workout plans, activity tracking, nutrition diary, wearable integrations, and social motivation features.

## Project modules

- `api-gateway` - unified API, auth token handling, orchestration workflow `log_workout`
- `user-service` - user profiles, anthropometry, goals, workout history
- `workout-service` - ready workout programs, adaptation for user profile, video instructions
- `tracking-service` - manual logs, Garmin/Fitbit/Apple Health sync endpoints, auto activity recognition
- `nutrition-service` - product catalog, calorie/macronutrient calculation, meal planning
- `social-service` - friends, feed, challenges, discussions, achievements checks
- `analytics-service` - progress statistics, charts, adaptive recommendations, async recalculation
- `notification-service` - reminders and achievement notifications
- `frontend` - React dashboard for FitLife web app
- `mobile` - React Native architecture notes for offline workouts mode

## Optional improvements covered

- Group A: exercise recognition endpoint (`/activities/recognize`), adaptive load recommendations
- Group B: wearable sync endpoints + MyFitnessPal sync + export endpoint
- Group C: video cache planning, parallel device processing plan, sharding plan, async stats recalc
- Group D: mobile offline concept, gamification via achievements/challenges

## Quality targets

- Program loading target: `< 2 sec` (`target_load_seconds` exposed by workout service)
- Calorie accuracy target: `±10%` (`/quality/calorie-accuracy`)
- Scalability target: `1,000,000 users` (`/analytics/sharding-plan`)

## Local run

```bash
cd FitLife
docker compose up --build -d
```

## Useful URLs

- Frontend: `http://localhost:5180`
- API Gateway health: `http://localhost:8500/health`
- All services health: `http://localhost:8500/services/health`
- Swagger gateway: `http://localhost:8500/docs`

## Validation

```bash
python -m ruff check .
python -m pytest -q
docker compose config
```

## Demo workflow

```bash
python scripts/demo_pipeline.py
```
