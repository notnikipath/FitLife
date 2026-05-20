
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.fitlife_common import ActivityType, LogWorkoutWorkflowResult, Role, Settings, sign_token, verify_token


class GatewaySettings(BaseSettings):
    service_name: str = "api-gateway"
    service_port: int = 8500

    user_service_url: str = "http://user-service:8501"
    workout_service_url: str = "http://workout-service:8502"
    tracking_service_url: str = "http://tracking-service:8503"
    nutrition_service_url: str = "http://nutrition-service:8504"
    social_service_url: str = "http://social-service:8505"
    analytics_service_url: str = "http://analytics-service:8506"
    notification_service_url: str = "http://notification-service:8507"

    jwt_secret: str = Settings().jwt_secret
    token_exp_minutes: int = 240

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = GatewaySettings()
app = FastAPI(title="FitLife API Gateway", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5180",
        "http://127.0.0.1:5180",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuthRequest(BaseModel):
    user_id: str
    role: Role
    language: str = Field(default="ru", pattern="^(ru|en)$")


class LogWorkoutRequest(BaseModel):
    user_id: str
    activity_type: ActivityType
    duration_minutes: int = Field(gt=0, le=720)
    distance_km: float = Field(default=0, ge=0)
    weight_kg: float = Field(default=70, gt=25)
    intensity: float = Field(default=1.0, ge=0.4, le=2.5)
    notes: str = ""


AuthRequest.model_rebuild()
LogWorkoutRequest.model_rebuild()


async def _post_json(client: httpx.AsyncClient, url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(url, json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = await client.get(url, params=params)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


async def _get_json_or_default(
    client: httpx.AsyncClient,
    url: str,
    default_payload: dict[str, Any],
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        return await _get_json(client, url, params=params)
    except HTTPException as exc:
        fallback = dict(default_payload)
        fallback["_error"] = f"HTTP {exc.status_code}: {exc.detail}"
        return fallback
    except httpx.HTTPError as exc:
        fallback = dict(default_payload)
        fallback["_error"] = str(exc)
        return fallback


def _service_urls() -> dict[str, str]:
    return {
        "user": settings.user_service_url,
        "workout": settings.workout_service_url,
        "tracking": settings.tracking_service_url,
        "nutrition": settings.nutrition_service_url,
        "social": settings.social_service_url,
        "analytics": settings.analytics_service_url,
        "notification": settings.notification_service_url,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/auth/token")
async def issue_token(request: AuthRequest) -> dict[str, str]:
    token = sign_token(
        {"sub": request.user_id, "role": request.role.value, "language": request.language},
        settings.jwt_secret,
        exp_minutes=settings.token_exp_minutes,
    )
    return {"access_token": token, "token_type": "Bearer"}


@app.post("/auth/verify")
async def verify_auth(token: str) -> dict[str, Any]:
    payload = verify_token(token, settings.jwt_secret)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


@app.get("/services/health")
async def service_health() -> dict[str, Any]:
    statuses: dict[str, Any] = {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, base_url in _service_urls().items():
            try:
                statuses[name] = await _get_json(client, f"{base_url}/health")
            except HTTPException as exc:
                statuses[name] = {"status": "error", "detail": exc.detail}
            except httpx.HTTPError as exc:
                statuses[name] = {"status": "error", "detail": str(exc)}
    return statuses


@app.post("/workflow/log-workout")
async def log_workout_workflow(request: LogWorkoutRequest) -> dict[str, Any]:
    notifications: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=25.0) as client:
        workout = await _post_json(
            client,
            f"{settings.tracking_service_url}/activities/manual",
            {
                "user_id": request.user_id,
                "activity_type": request.activity_type.value,
                "duration_minutes": request.duration_minutes,
                "distance_km": request.distance_km,
                "weight_kg": request.weight_kg,
                "intensity": request.intensity,
                "notes": request.notes,
            },
        )
        stats = await _post_json(
            client,
            f"{settings.analytics_service_url}/analytics/update-user-stats",
            {"user_id": request.user_id, "activity": workout},
        )
        achievement_result = await _post_json(
            client,
            f"{settings.social_service_url}/achievements/check",
            {"user_id": request.user_id, "activity": workout},
        )
        achievements = achievement_result.get("achievements", [])
        if achievements:
            titles = ", ".join(item["title"] for item in achievements)
            notification = await _post_json(
                client,
                f"{settings.notification_service_url}/notifications/send",
                {
                    "user_id": request.user_id,
                    "channel": "push",
                    "message": f"New achievements: {titles}",
                },
            )
            notifications.append(notification)

        recommendation = await _get_json(
            client,
            f"{settings.analytics_service_url}/analytics/recommendations/{request.user_id}",
        )

        try:
            await _post_json(
                client,
                f"{settings.user_service_url}/users/{request.user_id}/history",
                {"activity": workout},
            )
        except HTTPException:
            pass

    result = LogWorkoutWorkflowResult(
        workout=workout,
        stats=stats,
        achievements=achievements,
        recommendation=recommendation,
        notifications=notifications,
    )
    return result.model_dump(mode="json")


@app.get("/dashboard/{user_id}")
async def dashboard(user_id: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        profile = await _get_json_or_default(
            client,
            f"{settings.user_service_url}/users/{user_id}",
            {"user_id": user_id, "full_name": user_id},
        )
        activities = await _get_json_or_default(
            client,
            f"{settings.tracking_service_url}/activities/{user_id}",
            {"user_id": user_id, "count": 0, "activities": []},
        )
        nutrition = await _get_json_or_default(
            client,
            f"{settings.nutrition_service_url}/nutrition/summary/{user_id}",
            {"user_id": user_id, "calories": 0, "protein": 0, "fat": 0, "carbs": 0, "meals": 0},
        )
        social_feed = await _get_json_or_default(
            client,
            f"{settings.social_service_url}/feed/{user_id}",
            {"user_id": user_id, "count": 0, "items": []},
        )
        progress = await _get_json_or_default(
            client,
            f"{settings.analytics_service_url}/analytics/progress/{user_id}",
            {
                "user_id": user_id,
                "stats": {
                    "workouts_total": 0,
                    "total_duration_minutes": 0,
                    "total_calories": 0,
                    "weekly_load": 0,
                },
            },
        )
        recommendations = await _get_json_or_default(
            client,
            f"{settings.analytics_service_url}/analytics/recommendations/{user_id}",
            {"user_id": user_id, "next_activity": "Rest day", "comment": "No recommendation yet."},
        )
        notifications = await _get_json_or_default(
            client,
            f"{settings.notification_service_url}/notifications/{user_id}",
            {"user_id": user_id, "count": 0, "items": []},
        )

    return {
        "profile": profile,
        "activities": activities,
        "nutrition": nutrition,
        "social_feed": social_feed,
        "progress": progress,
        "recommendations": recommendations,
        "notifications": notifications,
    }
