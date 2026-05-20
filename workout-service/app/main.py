
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.fitlife_common import (
    ActivityType,
    Settings,
    UserProfile,
    WorkoutExercise,
    WorkoutProgram,
    adapt_program_volume,
    video_cache_plan,
)

settings = Settings(service_name="workout-service", service_port=8502)
app = FastAPI(title="FitLife Workout Service", version="1.0.0")


class PersonalizeRequest(BaseModel):
    user: UserProfile
    program_id: str | None = None
    preferred_activity: ActivityType | None = None


PersonalizeRequest.model_rebuild()


programs: dict[str, WorkoutProgram] = {
    "PRG-STRENGTH-01": WorkoutProgram(
        program_id="PRG-STRENGTH-01",
        title="Strength Foundation",
        activity_type=ActivityType.STRENGTH,
        difficulty="beginner",
        duration_weeks=8,
        exercises=[
            WorkoutExercise(
                name="Back Squat",
                activity_type=ActivityType.STRENGTH,
                sets=4,
                reps=8,
                video_url="https://fitlife/video/squat",
            ),
            WorkoutExercise(
                name="Bench Press",
                activity_type=ActivityType.STRENGTH,
                sets=4,
                reps=8,
                video_url="https://fitlife/video/bench",
            ),
        ],
    ),
    "PRG-CARDIO-RUN-01": WorkoutProgram(
        program_id="PRG-CARDIO-RUN-01",
        title="Run 5K Builder",
        activity_type=ActivityType.CARDIO_RUN,
        difficulty="intermediate",
        duration_weeks=6,
        exercises=[
            WorkoutExercise(
                name="Easy Run",
                activity_type=ActivityType.CARDIO_RUN,
                duration_minutes=30,
                video_url="https://fitlife/video/easy-run",
            ),
            WorkoutExercise(
                name="Intervals",
                activity_type=ActivityType.CARDIO_RUN,
                duration_minutes=25,
                video_url="https://fitlife/video/intervals",
            ),
        ],
    ),
    "PRG-CARDIO-CYCLE-01": WorkoutProgram(
        program_id="PRG-CARDIO-CYCLE-01",
        title="Cycling Endurance",
        activity_type=ActivityType.CARDIO_CYCLE,
        difficulty="intermediate",
        duration_weeks=6,
        exercises=[
            WorkoutExercise(
                name="Cadence Drill",
                activity_type=ActivityType.CARDIO_CYCLE,
                duration_minutes=35,
                video_url="https://fitlife/video/cadence",
            ),
            WorkoutExercise(
                name="Hill Session",
                activity_type=ActivityType.CARDIO_CYCLE,
                duration_minutes=40,
                video_url="https://fitlife/video/hills",
            ),
        ],
    ),
    "PRG-YOGA-01": WorkoutProgram(
        program_id="PRG-YOGA-01",
        title="Yoga Mobility Reset",
        activity_type=ActivityType.YOGA_STRETCH,
        difficulty="all-level",
        duration_weeks=4,
        exercises=[
            WorkoutExercise(
                name="Sun Salutation",
                activity_type=ActivityType.YOGA_STRETCH,
                duration_minutes=15,
                video_url="https://fitlife/video/sun",
            ),
            WorkoutExercise(
                name="Deep Stretch",
                activity_type=ActivityType.YOGA_STRETCH,
                duration_minutes=20,
                video_url="https://fitlife/video/stretch",
            ),
        ],
    ),
    "PRG-FUNCTIONAL-01": WorkoutProgram(
        program_id="PRG-FUNCTIONAL-01",
        title="Functional Athlete",
        activity_type=ActivityType.FUNCTIONAL,
        difficulty="advanced",
        duration_weeks=8,
        exercises=[
            WorkoutExercise(
                name="Kettlebell Complex",
                activity_type=ActivityType.FUNCTIONAL,
                sets=5,
                reps=10,
                video_url="https://fitlife/video/kb",
            ),
            WorkoutExercise(
                name="Burpee Ladder",
                activity_type=ActivityType.FUNCTIONAL,
                duration_minutes=18,
                video_url="https://fitlife/video/burpee",
            ),
        ],
    ),
    "PRG-SWIM-01": WorkoutProgram(
        program_id="PRG-SWIM-01",
        title="Swim Technique + Pace",
        activity_type=ActivityType.SWIMMING,
        difficulty="intermediate",
        duration_weeks=7,
        exercises=[
            WorkoutExercise(
                name="Freestyle Drill",
                activity_type=ActivityType.SWIMMING,
                duration_minutes=30,
                video_url="https://fitlife/video/freestyle",
            ),
            WorkoutExercise(
                name="Pace Repeats",
                activity_type=ActivityType.SWIMMING,
                duration_minutes=25,
                video_url="https://fitlife/video/pace",
            ),
        ],
    ),
}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/programs")
async def list_programs(activity_type: ActivityType | None = None) -> dict[str, Any]:
    items = []
    for program in programs.values():
        if activity_type and program.activity_type != activity_type:
            continue
        items.append(program.model_dump(mode="json"))
    return {
        "items": items,
        "count": len(items),
        "target_load_seconds": settings.program_load_target_seconds,
    }


@app.get("/programs/{program_id}")
async def get_program(program_id: str) -> dict[str, Any]:
    program = programs.get(program_id)
    if program is None:
        raise HTTPException(status_code=404, detail="Program not found")
    return program.model_dump(mode="json")


@app.post("/programs/personalize")
async def personalize_program(request: PersonalizeRequest) -> dict[str, Any]:
    selected = None
    if request.program_id:
        selected = programs.get(request.program_id)
    elif request.preferred_activity:
        selected = next(
            (item for item in programs.values() if item.activity_type == request.preferred_activity),
            None,
        )
    else:
        selected = next(
            (item for item in programs.values() if item.activity_type == request.user.goals.focus_activity),
            None,
        )
    if selected is None:
        raise HTTPException(status_code=404, detail="Matching program not found")
    adapted = adapt_program_volume(selected, request.user)
    return adapted.model_dump(mode="json")


@app.get("/videos/{activity_type}")
async def video_library(activity_type: ActivityType) -> dict[str, Any]:
    entries = []
    for program in programs.values():
        if program.activity_type != activity_type:
            continue
        for exercise in program.exercises:
            entries.append({"exercise": exercise.name, "video_url": exercise.video_url})
    return {"activity_type": activity_type.value, "items": entries, "count": len(entries)}


@app.get("/cache/video-plan")
async def cache_plan(videos: int = 1200, edge_nodes: int = 4) -> dict[str, int]:
    return video_cache_plan(videos, edge_nodes)
