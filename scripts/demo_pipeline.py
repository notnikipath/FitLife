from __future__ import annotations

import json

import httpx

GATEWAY = "http://localhost:8500"


def main() -> None:
    payload = {
        "user_id": "USR-DEMO",
        "activity_type": "functional",
        "duration_minutes": 48,
        "distance_km": 0,
        "weight_kg": 78,
        "intensity": 1.1,
        "notes": "demo pipeline",
    }
    with httpx.Client(timeout=20.0) as client:
        workflow = client.post(f"{GATEWAY}/workflow/log-workout", json=payload)
        workflow.raise_for_status()
        dashboard = client.get(f"{GATEWAY}/dashboard/USR-DEMO")
        dashboard.raise_for_status()

    print("Workflow result:")
    print(json.dumps(workflow.json(), ensure_ascii=False, indent=2))
    print("\nDashboard snapshot:")
    print(json.dumps(dashboard.json(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
