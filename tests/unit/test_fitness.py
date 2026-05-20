from shared.fitlife_common import estimate_calories, parallel_processing_plan, recognize_activity
from shared.fitlife_common.schemas import ActivityType


def test_estimate_calories_positive() -> None:
    value = estimate_calories(ActivityType.CARDIO_RUN, 30, 75, 1.0)
    assert value > 0


def test_recognize_activity_swim() -> None:
    activity = recognize_activity({"strokes_per_min": 38, "cadence": 0, "heart_rate": 132})
    assert activity == ActivityType.SWIMMING


def test_parallel_processing_plan_workers() -> None:
    plan = parallel_processing_plan(12000, 14)
    assert plan["workers"] >= 2
    assert plan["batch_size"] >= 25
