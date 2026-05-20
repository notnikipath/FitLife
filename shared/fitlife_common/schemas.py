from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Role(str, Enum):
    USER = "user"
    COACH = "coach"
    ADMIN = "admin"


class ActivityType(str, Enum):
    STRENGTH = "strength"
    CARDIO_RUN = "cardio_run"
    CARDIO_CYCLE = "cardio_cycle"
    YOGA_STRETCH = "yoga_stretch"
    FUNCTIONAL = "functional"
    SWIMMING = "swimming"


class WearableProvider(str, Enum):
    MANUAL = "manual"
    GARMIN = "garmin"
    FITBIT = "fitbit"
    APPLE_HEALTH = "apple_health"


class NotificationChannel(str, Enum):
    PUSH = "push"
    EMAIL = "email"
    IN_APP = "in_app"


class Anthropometry(BaseModel):
    height_cm: int = Field(gt=80, lt=260)
    weight_kg: float = Field(gt=25, lt=400)
    age: int = Field(gt=10, lt=100)
    body_fat_pct: float | None = Field(default=None, ge=2, le=70)


class GoalProfile(BaseModel):
    target_weight_kg: float = Field(gt=25, lt=400)
    training_days_per_week: int = Field(ge=1, le=14)
    focus_activity: ActivityType


class UserProfile(BaseModel):
    user_id: str
    full_name: str
    anthropometry: Anthropometry
    goals: GoalProfile
    activity_level: str = "moderate"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WorkoutExercise(BaseModel):
    name: str
    activity_type: ActivityType
    sets: int = Field(default=0, ge=0)
    reps: int = Field(default=0, ge=0)
    duration_minutes: int = Field(default=0, ge=0)
    video_url: str


class WorkoutProgram(BaseModel):
    program_id: str
    title: str
    activity_type: ActivityType
    difficulty: str
    duration_weeks: int = Field(ge=1, le=52)
    exercises: list[WorkoutExercise] = Field(default_factory=list)
    adaptive_rules: dict[str, Any] = Field(default_factory=dict)


class WorkoutLog(BaseModel):
    activity_id: str
    user_id: str
    activity_type: ActivityType
    duration_minutes: int = Field(gt=0, le=720)
    calories_burned: int = Field(ge=0)
    distance_km: float = Field(default=0, ge=0)
    source: WearableProvider = WearableProvider.MANUAL
    auto_recognized: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class Product(BaseModel):
    product_id: str
    name: str
    kcal_per_100g: float = Field(ge=0)
    protein_per_100g: float = Field(ge=0)
    fat_per_100g: float = Field(ge=0)
    carbs_per_100g: float = Field(ge=0)


class MealItem(BaseModel):
    product_id: str
    grams: float = Field(gt=0, le=2000)


class MealTotals(BaseModel):
    calories: float
    protein: float
    fat: float
    carbs: float


class Achievement(BaseModel):
    achievement_id: str
    title: str
    description: str
    unlocked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserStats(BaseModel):
    user_id: str
    workouts_total: int = 0
    total_duration_minutes: int = 0
    total_calories: int = 0
    weekly_load: float = 0
    streak_days: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WorkoutRecommendation(BaseModel):
    user_id: str
    next_activity: ActivityType
    target_duration_minutes: int
    intensity: str
    comment: str


class NotificationPayload(BaseModel):
    user_id: str
    channel: NotificationChannel
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LogWorkoutWorkflowResult(BaseModel):
    workout: dict[str, Any]
    stats: dict[str, Any]
    achievements: list[dict[str, Any]]
    recommendation: dict[str, Any]
    notifications: list[dict[str, Any]]
