# FitLife API Snapshot

## Gateway

- `POST /auth/token`
- `POST /auth/verify`
- `GET /services/health`
- `POST /workflow/log-workout`
- `GET /dashboard/{user_id}`

## User service

- `GET /users`
- `GET /users/{user_id}`
- `POST /users`
- `GET /users/{user_id}/history`
- `POST /users/{user_id}/history`

## Workout service

- `GET /programs`
- `GET /programs/{program_id}`
- `POST /programs/personalize`
- `GET /videos/{activity_type}`
- `GET /cache/video-plan`

## Tracking service

- `POST /activities/manual`
- `POST /activities/wearables/sync`
- `POST /activities/recognize`
- `GET /activities/{user_id}`
- `GET /processing/parallel-plan`

## Nutrition service

- `GET /products`
- `POST /nutrition/calculate`
- `POST /nutrition/plan`
- `POST /integrations/myfitnesspal/sync`
- `GET /export/{user_id}/excel`

## Social service

- `GET /friends/{user_id}`
- `GET /feed/{user_id}`
- `POST /feed/post`
- `GET /challenges`
- `POST /achievements/check`

## Analytics service

- `POST /analytics/update-user-stats`
- `GET /analytics/progress/{user_id}`
- `GET /analytics/charts/{user_id}`
- `GET /analytics/recommendations/{user_id}`
- `POST /analytics/async-recalc`

## Notification service

- `POST /notifications/send`
- `POST /notifications/reminder`
- `GET /notifications/{user_id}`
