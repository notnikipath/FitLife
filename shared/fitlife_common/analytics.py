from __future__ import annotations

from .schemas import ActivityType, UserStats, WorkoutRecommendation


def calculate_weekly_load(total_duration_minutes: int, workouts_total: int) -> float:
    if workouts_total <= 0:
        return 0.0
    return round((total_duration_minutes / workouts_total) * 0.7 + workouts_total * 2.5, 2)


def build_recommendation(user_id: str, stats: UserStats) -> WorkoutRecommendation:
    if stats.weekly_load < 45:
        return WorkoutRecommendation(
            user_id=user_id,
            next_activity=ActivityType.FUNCTIONAL,
            target_duration_minutes=35,
            intensity="moderate",
            comment="Можно плавно повысить нагрузку для устойчивого прогресса.",
        )
    if stats.weekly_load < 75:
        return WorkoutRecommendation(
            user_id=user_id,
            next_activity=ActivityType.CARDIO_RUN,
            target_duration_minutes=40,
            intensity="moderate-high",
            comment="Хорошая форма. Добавим интервальное кардио.",
        )
    return WorkoutRecommendation(
        user_id=user_id,
        next_activity=ActivityType.YOGA_STRETCH,
        target_duration_minutes=25,
        intensity="recovery",
        comment="Нагрузка высокая. Рекомендован восстановительный день.",
    )


def chart_points(stats: UserStats) -> list[dict[str, float | int]]:
    base = max(stats.total_duration_minutes // max(stats.workouts_total, 1), 10)
    return [
        {"week": 1, "duration": max(10, base - 12), "calories": max(100, stats.total_calories // 4)},
        {"week": 2, "duration": max(15, base - 6), "calories": max(150, stats.total_calories // 3)},
        {"week": 3, "duration": base, "calories": max(220, stats.total_calories // 2)},
        {"week": 4, "duration": min(base + 8, base * 2), "calories": max(300, stats.total_calories)},
    ]


def shard_plan(users: int, target_shard_size: int = 100_000) -> dict[str, int]:
    shards = max(1, (users + target_shard_size - 1) // target_shard_size)
    return {"users": users, "target_shard_size": target_shard_size, "shards": shards}
