from __future__ import annotations

from .schemas import ActivityType, UserProfile, WorkoutProgram

MET_VALUES: dict[ActivityType, float] = {
    ActivityType.STRENGTH: 6.0,
    ActivityType.CARDIO_RUN: 9.8,
    ActivityType.CARDIO_CYCLE: 8.2,
    ActivityType.YOGA_STRETCH: 3.0,
    ActivityType.FUNCTIONAL: 7.4,
    ActivityType.SWIMMING: 8.0,
}


def estimate_calories(
    activity_type: ActivityType,
    duration_minutes: int,
    weight_kg: float,
    intensity: float = 1.0,
) -> int:
    met = MET_VALUES.get(activity_type, 5.0)
    kcal = met * 3.5 * weight_kg / 200 * duration_minutes * max(intensity, 0.4)
    return max(1, round(kcal))


def recognize_activity(sensor_payload: dict[str, float]) -> ActivityType:
    strokes = sensor_payload.get("strokes_per_min", 0)
    cadence = sensor_payload.get("cadence", 0)
    pose_stability = sensor_payload.get("pose_stability", 0)
    heart_rate = sensor_payload.get("heart_rate", 0)
    if strokes >= 30:
        return ActivityType.SWIMMING
    if pose_stability >= 0.8 and heart_rate < 120:
        return ActivityType.YOGA_STRETCH
    if cadence >= 160:
        return ActivityType.CARDIO_RUN
    if cadence >= 90:
        return ActivityType.CARDIO_CYCLE
    if heart_rate >= 150:
        return ActivityType.FUNCTIONAL
    return ActivityType.STRENGTH


def adapt_program_volume(program: WorkoutProgram, user: UserProfile) -> WorkoutProgram:
    scale = 1.0
    if user.goals.training_days_per_week >= 6:
        scale = 1.2
    elif user.goals.training_days_per_week <= 3:
        scale = 0.85
    cloned = program.model_copy(deep=True)
    for exercise in cloned.exercises:
        if exercise.sets > 0:
            exercise.sets = max(1, round(exercise.sets * scale))
        if exercise.reps > 0:
            exercise.reps = max(4, round(exercise.reps * scale))
        if exercise.duration_minutes > 0:
            exercise.duration_minutes = max(5, round(exercise.duration_minutes * scale))
    cloned.adaptive_rules["volume_scale"] = scale
    cloned.adaptive_rules["goal_activity"] = user.goals.focus_activity.value
    return cloned


def video_cache_plan(video_count: int, edge_nodes: int) -> dict[str, int]:
    nodes = max(1, edge_nodes)
    chunk = max(10, video_count // nodes) if video_count > 0 else 10
    return {"video_count": video_count, "edge_nodes": nodes, "chunk_per_node": chunk}


def parallel_processing_plan(events: int, device_streams: int) -> dict[str, int]:
    workers = min(64, max(2, device_streams * 2, events // 250))
    batch_size = max(25, events // workers) if events > 0 else 25
    return {"workers": workers, "batch_size": batch_size, "events": events}
