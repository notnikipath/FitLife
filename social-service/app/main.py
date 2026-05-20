
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from shared.fitlife_common import Achievement, Settings

settings = Settings(service_name="social-service", service_port=8505)
app = FastAPI(title="FitLife Social Service", version="1.0.0")


class AddFriendRequest(BaseModel):
    user_id: str
    friend_id: str


class FeedPostRequest(BaseModel):
    user_id: str
    text: str
    achievement_title: str | None = None


class ChallengeJoinRequest(BaseModel):
    user_id: str
    challenge_id: str


class DiscussionMessageRequest(BaseModel):
    user_id: str
    text: str


class AchievementCheckRequest(BaseModel):
    user_id: str
    activity: dict[str, Any] = Field(default_factory=dict)


AddFriendRequest.model_rebuild()
FeedPostRequest.model_rebuild()
ChallengeJoinRequest.model_rebuild()
DiscussionMessageRequest.model_rebuild()
AchievementCheckRequest.model_rebuild()


friends: dict[str, set[str]] = {"USR-DEMO": {"USR-FRIEND-1", "USR-FRIEND-2"}}
feed: list[dict[str, Any]] = [
    {
        "user_id": "USR-FRIEND-1",
        "text": "Closed 10km run today.",
        "created_at": datetime.now(UTC).isoformat(),
    }
]

challenges: list[dict[str, Any]] = [
    {"challenge_id": "CH-10K-STEPS", "title": "10k Steps Daily", "participants": 320},
    {"challenge_id": "CH-7DAY-STREAK", "title": "7 Day Workout Streak", "participants": 185},
]

discussions: dict[str, list[dict[str, Any]]] = {"recovery": []}
user_activity_counter: dict[str, int] = {"USR-DEMO": 1}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/friends/{user_id}")
async def get_friends(user_id: str) -> dict[str, Any]:
    items = sorted(friends.get(user_id, set()))
    return {"user_id": user_id, "items": items, "count": len(items)}


@app.post("/friends/add")
async def add_friend(request: AddFriendRequest) -> dict[str, Any]:
    friends.setdefault(request.user_id, set()).add(request.friend_id)
    friends.setdefault(request.friend_id, set()).add(request.user_id)
    return {"user_id": request.user_id, "friend_id": request.friend_id, "status": "added"}


@app.get("/feed/{user_id}")
async def get_feed(user_id: str, limit: int = 20) -> dict[str, Any]:
    circle = friends.get(user_id, set()) | {user_id}
    items = [item for item in feed if item["user_id"] in circle][-limit:]
    return {"user_id": user_id, "items": items, "count": len(items)}


@app.post("/feed/post")
async def post_feed(request: FeedPostRequest) -> dict[str, Any]:
    item = {
        "user_id": request.user_id,
        "text": request.text,
        "achievement_title": request.achievement_title,
        "created_at": datetime.now(UTC).isoformat(),
    }
    feed.append(item)
    return item


@app.get("/challenges")
async def list_challenges() -> dict[str, Any]:
    return {"items": challenges, "count": len(challenges)}


@app.post("/challenges/join")
async def join_challenge(request: ChallengeJoinRequest) -> dict[str, Any]:
    for challenge in challenges:
        if challenge["challenge_id"] == request.challenge_id:
            challenge["participants"] += 1
            return {"status": "joined", "challenge": challenge, "user_id": request.user_id}
    return {"status": "not_found", "challenge_id": request.challenge_id}


@app.get("/discussions/{topic}")
async def discussion(topic: str, limit: int = 50) -> dict[str, Any]:
    items = discussions.get(topic, [])[-limit:]
    return {"topic": topic, "items": items, "count": len(items)}


@app.post("/discussions/{topic}/messages")
async def post_discussion(topic: str, request: DiscussionMessageRequest) -> dict[str, Any]:
    entry = {
        "user_id": request.user_id,
        "text": request.text,
        "created_at": datetime.now(UTC).isoformat(),
    }
    discussions.setdefault(topic, []).append(entry)
    return entry


@app.post("/achievements/check")
async def check_achievements(request: AchievementCheckRequest) -> dict[str, Any]:
    user_activity_counter[request.user_id] = user_activity_counter.get(request.user_id, 0) + 1
    achievements: list[Achievement] = []
    if user_activity_counter[request.user_id] == 1:
        achievements.append(
            Achievement(
                achievement_id="ACH-FIRST",
                title="First Workout",
                description="Completed first workout.",
            )
        )
    duration = int(request.activity.get("duration_minutes", 0))
    calories = int(request.activity.get("calories_burned", 0))
    if duration >= 60:
        achievements.append(
            Achievement(
                achievement_id="ACH-ENDURANCE",
                title="Endurance Hour",
                description="Trained 60+ minutes.",
            )
        )
    if calories >= 500:
        achievements.append(
            Achievement(
                achievement_id="ACH-BURN",
                title="Calorie Crusher",
                description="Burned 500+ calories.",
            )
        )
    if achievements:
        for achievement in achievements:
            feed.append(
                {
                    "user_id": request.user_id,
                    "text": f"Unlocked: {achievement.title}",
                    "achievement_title": achievement.title,
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )
    return {
        "user_id": request.user_id,
        "achievements": [item.model_dump(mode="json") for item in achievements],
    }
