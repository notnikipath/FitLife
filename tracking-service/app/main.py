
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from shared.fitlife_common import (
    ActivityType,
    Settings,
    WearableProvider,
    WorkoutLog,
    estimate_calories,
    parallel_processing_plan,
    recognize_activity,
)

settings = Settings(service_name="tracking-service", service_port=8503)
app = FastAPI(title="FitLife Tracking Service", version="1.0.0")


class ManualActivityRequest(BaseModel):
    user_id: str
    activity_type: ActivityType
    duration_minutes: int = Field(gt=0, le=720)
    distance_km: float = Field(default=0, ge=0)
    calories_burned: int | None = Field(default=None, ge=0)
    weight_kg: float = Field(default=70, gt=25)
    intensity: float = Field(default=1.0, ge=0.4, le=2.5)
    notes: str = ""


class WearableSession(BaseModel):
    activity_type: ActivityType
    duration_minutes: int = Field(gt=0, le=720)
    distance_km: float = Field(default=0, ge=0)
    calories_burned: int | None = Field(default=None, ge=0)


class WearableSyncRequest(BaseModel):
    provider: WearableProvider
    user_id: str
    sessions: list[WearableSession]
    payload: dict[str, Any] = Field(default_factory=dict)


class RecognizeRequest(BaseModel):
    user_id: str
    sensor_payload: dict[str, float] = Field(default_factory=dict)
    duration_minutes: int = Field(default=30, gt=0, le=720)
    weight_kg: float = Field(default=70, gt=25)


ManualActivityRequest.model_rebuild()
WearableSession.model_rebuild()
WearableSyncRequest.model_rebuild()
RecognizeRequest.model_rebuild()


activities_by_user: dict[str, list[WorkoutLog]] = {
    "USR-DEMO": [
        WorkoutLog(
            activity_id="ACT-DEMO-TRACK-1",
            user_id="USR-DEMO",
            activity_type=ActivityType.STRENGTH,
            duration_minutes=45,
            calories_burned=390,
            distance_km=0,
            source=WearableProvider.MANUAL,
            metadata={"notes": "upper body"},
        )
    ]
}

activity_index: dict[str, WorkoutLog] = {"ACT-DEMO-TRACK-1": activities_by_user["USR-DEMO"][0]}


def _store(log: WorkoutLog) -> WorkoutLog:
    activities_by_user.setdefault(log.user_id, []).append(log)
    activity_index[log.activity_id] = log
    return log


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/activities/manual")
async def log_manual_activity(request: ManualActivityRequest) -> dict[str, Any]:
    calories = request.calories_burned
    if calories is None:
        calories = estimate_calories(
            request.activity_type,
            request.duration_minutes,
            request.weight_kg,
            request.intensity,
        )
    log = WorkoutLog(
        activity_id=f"ACT-{uuid4().hex[:10].upper()}",
        user_id=request.user_id,
        activity_type=request.activity_type,
        duration_minutes=request.duration_minutes,
        calories_burned=calories,
        distance_km=request.distance_km,
        source=WearableProvider.MANUAL,
        metadata={"notes": request.notes},
    )
    _store(log)
    return log.model_dump(mode="json")


@app.post("/activities/wearables/sync")
async def sync_wearable(request: WearableSyncRequest) -> dict[str, Any]:
    if request.provider == WearableProvider.MANUAL:
        raise HTTPException(status_code=400, detail="Use dedicated manual endpoint")
    accepted = 0
    items: list[dict[str, Any]] = []
    for session in request.sessions:
        calories = session.calories_burned
        if calories is None:
            calories = estimate_calories(session.activity_type, session.duration_minutes, 70, 1.0)
        log = WorkoutLog(
            activity_id=f"ACT-{uuid4().hex[:10].upper()}",
            user_id=request.user_id,
            activity_type=session.activity_type,
            duration_minutes=session.duration_minutes,
            calories_burned=calories,
            distance_km=session.distance_km,
            source=request.provider,
            metadata={"provider_payload": request.payload},
        )
        _store(log)
        items.append(log.model_dump(mode="json"))
        accepted += 1
    return {"provider": request.provider.value, "accepted": accepted, "items": items}


@app.post("/activities/recognize")
async def recognize_and_log(request: RecognizeRequest) -> dict[str, Any]:
    recognized = recognize_activity(request.sensor_payload)
    calories = estimate_calories(recognized, request.duration_minutes, request.weight_kg, 1.05)
    log = WorkoutLog(
        activity_id=f"ACT-{uuid4().hex[:10].upper()}",
        user_id=request.user_id,
        activity_type=recognized,
        duration_minutes=request.duration_minutes,
        calories_burned=calories,
        source=WearableProvider.MANUAL,
        auto_recognized=True,
        metadata={"sensor_payload": request.sensor_payload},
    )
    _store(log)
    return {"recognized_activity": recognized.value, "log": log.model_dump(mode="json")}


@app.get("/activities/{user_id}")
async def user_activities(user_id: str, limit: int = 50) -> dict[str, Any]:
    items = [item.model_dump(mode="json") for item in activities_by_user.get(user_id, [])][-limit:]
    total_calories = sum(int(item["calories_burned"]) for item in items)
    return {"user_id": user_id, "items": items, "count": len(items), "total_calories": total_calories}


@app.get("/activities/item/{activity_id}")
async def activity_by_id(activity_id: str) -> dict[str, Any]:
    activity = activity_index.get(activity_id)
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity.model_dump(mode="json")


@app.get("/processing/parallel-plan")
async def processing_plan(events: int = 10000, device_streams: int = 12) -> dict[str, int]:
    return parallel_processing_plan(events, device_streams)


@app.get("/storage/meta")
async def storage_meta() -> dict[str, Any]:
    return {
        "mongodb": settings.mongodb_uri,
        "collection": "activity_logs",
        "updated_at": datetime.now(UTC).isoformat(),
    }
