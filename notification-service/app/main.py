
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from shared.fitlife_common import NotificationChannel, NotificationPayload, Settings

settings = Settings(service_name="notification-service", service_port=8507)
app = FastAPI(title="FitLife Notification Service", version="1.0.0")


class SendNotificationRequest(BaseModel):
    user_id: str
    channel: NotificationChannel = NotificationChannel.PUSH
    message: str


SendNotificationRequest.model_rebuild()


history: dict[str, list[NotificationPayload]] = {"USR-DEMO": []}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/notifications/send")
async def send(request: SendNotificationRequest) -> dict[str, Any]:
    payload = NotificationPayload(user_id=request.user_id, channel=request.channel, message=request.message)
    history.setdefault(request.user_id, []).append(payload)
    return payload.model_dump(mode="json")


@app.post("/notifications/reminder")
async def reminder(user_id: str, text: str = "Time for your workout") -> dict[str, Any]:
    payload = NotificationPayload(user_id=user_id, channel=NotificationChannel.PUSH, message=text)
    history.setdefault(user_id, []).append(payload)
    return payload.model_dump(mode="json")


@app.get("/notifications/{user_id}")
async def list_notifications(user_id: str, limit: int = 50) -> dict[str, Any]:
    items = [item.model_dump(mode="json") for item in history.get(user_id, [])][-limit:]
    return {
        "user_id": user_id,
        "items": items,
        "count": len(items),
        "generated_at": datetime.now(UTC).isoformat(),
    }
