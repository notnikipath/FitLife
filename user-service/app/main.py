
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.fitlife_common import ActivityType, Anthropometry, GoalProfile, Settings, UserProfile

settings = Settings(service_name="user-service", service_port=8501)
app = FastAPI(title="FitLife User Service", version="1.0.0")


class UserProfileCreate(BaseModel):
    full_name: str
    anthropometry: Anthropometry
    goals: GoalProfile
    activity_level: str = "moderate"


class HistoryAppendRequest(BaseModel):
    activity: dict[str, Any]


UserProfileCreate.model_rebuild()
HistoryAppendRequest.model_rebuild()


users: dict[str, UserProfile] = {
    "USR-DEMO": UserProfile(
        user_id="USR-DEMO",
        full_name="Alex Fitness",
        anthropometry=Anthropometry(height_cm=178, weight_kg=78, age=29, body_fat_pct=17),
        goals=GoalProfile(
            target_weight_kg=74,
            training_days_per_week=5,
            focus_activity=ActivityType.FUNCTIONAL,
        ),
        activity_level="active",
    )
}

history_store: dict[str, list[dict[str, Any]]] = {
    "USR-DEMO": [
        {
            "activity_id": "ACT-DEMO-1",
            "activity_type": ActivityType.STRENGTH.value,
            "duration_minutes": 45,
            "calories_burned": 380,
            "created_at": datetime.now(UTC).isoformat(),
        }
    ]
}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/users")
async def list_users() -> dict[str, Any]:
    items = [profile.model_dump(mode="json") for profile in users.values()]
    return {"items": items, "count": len(items)}


@app.get("/users/{user_id}")
async def get_user(user_id: str) -> dict[str, Any]:
    profile = users.get(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="User not found")
    return profile.model_dump(mode="json")


@app.post("/users")
async def create_user(request: UserProfileCreate) -> dict[str, Any]:
    user_id = f"USR-{uuid4().hex[:8].upper()}"
    profile = UserProfile(
        user_id=user_id,
        full_name=request.full_name,
        anthropometry=request.anthropometry,
        goals=request.goals,
        activity_level=request.activity_level,
    )
    users[user_id] = profile
    history_store[user_id] = []
    return profile.model_dump(mode="json")


@app.get("/users/{user_id}/history")
async def get_history(user_id: str, limit: int = 30) -> dict[str, Any]:
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    items = history_store.get(user_id, [])[-limit:]
    return {"user_id": user_id, "items": items, "count": len(items)}


@app.post("/users/{user_id}/history")
async def append_history(user_id: str, request: HistoryAppendRequest) -> dict[str, Any]:
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    item = dict(request.activity)
    item.setdefault("activity_id", f"ACT-{uuid4().hex[:10].upper()}")
    item.setdefault("created_at", datetime.now(UTC).isoformat())
    history_store.setdefault(user_id, []).append(item)
    return {"user_id": user_id, "saved": item}
