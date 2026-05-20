# FitLife Architecture

## Overview

FitLife uses a microservice architecture for independent scaling of profile, workouts, tracking, nutrition, social interactions, analytics, and notifications.

## Services

- `api-gateway`: single entrypoint and orchestration workflows.
- `user-service`: profile data (anthropometry, goals, history).
- `workout-service`: ready programs + adaptation logic + video catalog.
- `tracking-service`: activity ingestion from manual and wearable sources.
- `nutrition-service`: product catalog, meal calculations, plans.
- `social-service`: friends, feed, challenges, discussions, achievements.
- `analytics-service`: progress metrics, charts, recommendations.
- `notification-service`: push/email/in-app alerts.

## Data layer

- PostgreSQL: transactional user, nutrition, and social entities.
- MongoDB: high-volume activity logs from devices.
- Redis: cache for hot data and session-like shared state.
- RabbitMQ: asynchronous events and decoupled background updates.

## Key workflow: log workout

1. `tracking-service` saves workout.
2. `analytics-service` updates user stats.
3. `social-service` checks achievements.
4. `notification-service` sends achievement notification.
5. `analytics-service` returns next workout recommendation.

## Non-functional targets

- Workout program load under 2 seconds.
- Calorie estimation error within ±10%.
- Horizontal scale to 1 million users.
