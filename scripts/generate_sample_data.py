from __future__ import annotations

import json
import random
from pathlib import Path

ACTIVITIES = [
    "strength",
    "cardio_run",
    "cardio_cycle",
    "yoga_stretch",
    "functional",
    "swimming",
]
SOURCES = ["manual", "garmin", "fitbit", "apple_health"]


def generate_event(i: int) -> dict[str, object]:
    activity = random.choice(ACTIVITIES)
    duration = random.randint(20, 75)
    distance = round(random.uniform(0, 10), 2) if "cardio" in activity or activity == "swimming" else 0
    calories = random.randint(180, 680)
    return {
        "event_id": f"EVT-{i:05d}",
        "user_id": f"USR-{random.randint(1, 500):04d}",
        "activity_type": activity,
        "duration_minutes": duration,
        "distance_km": distance,
        "calories_burned": calories,
        "source": random.choice(SOURCES),
    }


def main() -> None:
    random.seed(19)
    events = [generate_event(i) for i in range(1, 251)]
    out = Path("data/samples/fitness_events.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(events)} events -> {out}")


if __name__ == "__main__":
    main()
