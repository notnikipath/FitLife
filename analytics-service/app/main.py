
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from shared.fitlife_common import (
    Settings,
    UserStats,
    build_recommendation,
    calculate_weekly_load,
    chart_points,
    shard_plan,
)

settings = Settings(service_name="analytics-service", service_port=8506)
app = FastAPI(title="FitLife Analytics Service", version="1.0.0")


class UpdateStatsRequest(BaseModel):
    user_id: str
    activity: dict[str, Any] = Field(default_factory=dict)


class AsyncRecalcRequest(BaseModel):
    user_id: str


UpdateStatsRequest.model_rebuild()
AsyncRecalcRequest.model_rebuild()


stats_store: dict[str, UserStats] = {
    "USR-DEMO": UserStats(
        user_id="USR-DEMO",
        workouts_total=4,
        total_duration_minutes=180,
        total_calories=1520,
        weekly_load=68.0,
        streak_days=4,
    )
}

jobs: dict[str, dict[str, Any]] = {}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/analytics/update-user-stats")
async def update_user_stats(request: UpdateStatsRequest) -> dict[str, Any]:
    stats = stats_store.get(request.user_id, UserStats(user_id=request.user_id))
    duration = int(request.activity.get("duration_minutes", 0))
    calories = int(request.activity.get("calories_burned", 0))
    if duration > 0 or calories > 0:
        stats.workouts_total += 1
        stats.total_duration_minutes += duration
        stats.total_calories += calories
    stats.weekly_load = calculate_weekly_load(stats.total_duration_minutes, max(stats.workouts_total, 1))
    stats.streak_days = min(90, max(stats.streak_days, min(stats.workouts_total, 14)))
    stats.updated_at = datetime.now(UTC)
    stats_store[request.user_id] = stats
    return stats.model_dump(mode="json")


@app.get("/analytics/progress/{user_id}")
async def progress(user_id: str) -> dict[str, Any]:
    stats = stats_store.get(user_id, UserStats(user_id=user_id))
    return {
        "user_id": user_id,
        "stats": stats.model_dump(mode="json"),
        "quality_targets": {
            "program_load_seconds": settings.program_load_target_seconds,
            "calorie_accuracy_pct": settings.calorie_accuracy_tolerance_pct,
            "supported_users": settings.max_supported_users,
        },
    }


@app.get("/analytics/charts/{user_id}")
async def charts(user_id: str) -> dict[str, Any]:
    stats = stats_store.get(user_id, UserStats(user_id=user_id))
    return {"user_id": user_id, "points": chart_points(stats)}


@app.get("/analytics/recommendations/{user_id}")
async def recommendation(user_id: str) -> dict[str, Any]:
    stats = stats_store.get(user_id, UserStats(user_id=user_id))
    return build_recommendation(user_id, stats).model_dump(mode="json")


@app.post("/analytics/async-recalc")
async def async_recalc(request: AsyncRecalcRequest) -> dict[str, Any]:
    job_id = f"JOB-{uuid4().hex[:10].upper()}"
    stats = stats_store.get(request.user_id, UserStats(user_id=request.user_id))
    stats.weekly_load = calculate_weekly_load(stats.total_duration_minutes, max(stats.workouts_total, 1))
    stats.updated_at = datetime.now(UTC)
    stats_store[request.user_id] = stats
    jobs[job_id] = {
        "job_id": job_id,
        "user_id": request.user_id,
        "status": "completed",
        "started_at": datetime.now(UTC).isoformat(),
        "finished_at": datetime.now(UTC).isoformat(),
    }
    return jobs[job_id]


@app.get("/analytics/jobs/{job_id}")
async def job_status(job_id: str) -> dict[str, Any]:
    return jobs.get(job_id, {"job_id": job_id, "status": "not_found"})


@app.get("/analytics/sharding-plan")
async def sharding(users: int = 1000000, shard_size: int = 100000) -> dict[str, int]:
    return shard_plan(users, shard_size)
