from shared.fitlife_common import build_recommendation, calculate_weekly_load, shard_plan
from shared.fitlife_common.schemas import UserStats


def test_weekly_load() -> None:
    load = calculate_weekly_load(210, 5)
    assert load > 0


def test_recommendation_has_duration() -> None:
    stats = UserStats(user_id="USR", workouts_total=3, total_duration_minutes=120, total_calories=900, weekly_load=42)
    rec = build_recommendation("USR", stats)
    assert rec.target_duration_minutes > 0


def test_shard_plan() -> None:
    plan = shard_plan(1_000_000, 100_000)
    assert plan["shards"] == 10
