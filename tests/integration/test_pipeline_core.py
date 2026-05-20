from pathlib import Path

from fastapi.testclient import TestClient

from tests.integration.helpers import load_module

ROOT = Path(__file__).resolve().parents[2]

user_module = load_module("user_module", ROOT / "user-service" / "app" / "main.py")
workout_module = load_module("workout_module", ROOT / "workout-service" / "app" / "main.py")
tracking_module = load_module("tracking_module", ROOT / "tracking-service" / "app" / "main.py")
nutrition_module = load_module("nutrition_module", ROOT / "nutrition-service" / "app" / "main.py")
social_module = load_module("social_module", ROOT / "social-service" / "app" / "main.py")
analytics_module = load_module("analytics_module", ROOT / "analytics-service" / "app" / "main.py")
notification_module = load_module("notification_module", ROOT / "notification-service" / "app" / "main.py")

user_client = TestClient(user_module.app)
workout_client = TestClient(workout_module.app)
tracking_client = TestClient(tracking_module.app)
nutrition_client = TestClient(nutrition_module.app)
social_client = TestClient(social_module.app)
analytics_client = TestClient(analytics_module.app)
notification_client = TestClient(notification_module.app)


def test_profile_program_tracking_flow() -> None:
    profile_response = user_client.get("/users/USR-DEMO")
    assert profile_response.status_code == 200
    profile = profile_response.json()

    personalized = workout_client.post(
        "/programs/personalize",
        json={
            "user": profile,
            "preferred_activity": "functional",
        },
    )
    assert personalized.status_code == 200
    program = personalized.json()
    assert program["activity_type"] == "functional"

    tracked = tracking_client.post(
        "/activities/manual",
        json={
            "user_id": "USR-DEMO",
            "activity_type": "functional",
            "duration_minutes": 44,
            "weight_kg": 78,
            "distance_km": 0,
        },
    )
    assert tracked.status_code == 200
    workout = tracked.json()
    assert workout["calories_burned"] > 0

    history = user_client.post("/users/USR-DEMO/history", json={"activity": workout})
    assert history.status_code == 200


def test_analytics_social_nutrition_notifications_flow() -> None:
    activity = {
        "duration_minutes": 62,
        "calories_burned": 540,
        "activity_type": "cardio_run",
    }

    stats_response = analytics_client.post(
        "/analytics/update-user-stats",
        json={"user_id": "USR-DEMO", "activity": activity},
    )
    assert stats_response.status_code == 200

    achievements_response = social_client.post(
        "/achievements/check",
        json={"user_id": "USR-DEMO", "activity": activity},
    )
    assert achievements_response.status_code == 200
    achievements = achievements_response.json()["achievements"]
    assert len(achievements) >= 1

    notice = notification_client.post(
        "/notifications/send",
        json={
            "user_id": "USR-DEMO",
            "channel": "push",
            "message": "Achievement unlocked",
        },
    )
    assert notice.status_code == 200

    meal = nutrition_client.post(
        "/nutrition/calculate",
        json={
            "user_id": "USR-DEMO",
            "meal_name": "post-workout",
            "items": [
                {"product_id": "PRD-CHICK", "grams": 200},
                {"product_id": "PRD-RICE", "grams": 180},
            ],
        },
    )
    assert meal.status_code == 200
    assert meal.json()["totals"]["calories"] > 0

    recommendation = analytics_client.get("/analytics/recommendations/USR-DEMO")
    assert recommendation.status_code == 200
    assert recommendation.json()["target_duration_minutes"] > 0
