
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from shared.fitlife_common import (
    MealItem,
    Product,
    Settings,
    calculate_meal_totals,
    calorie_error_pct,
    macro_distribution,
)

settings = Settings(service_name="nutrition-service", service_port=8504)
app = FastAPI(title="FitLife Nutrition Service", version="1.0.0")


class MealCalculationRequest(BaseModel):
    user_id: str | None = None
    meal_name: str = "meal"
    items: list[MealItem]


class PlanRequest(BaseModel):
    user_id: str
    target_kcal: int = Field(ge=1200, le=5000)
    meals_per_day: int = Field(default=4, ge=2, le=8)
    excluded_products: list[str] = Field(default_factory=list)


class MyFitnessPalSyncRequest(BaseModel):
    user_id: str
    entries: list[dict[str, Any]] = Field(default_factory=list)


MealCalculationRequest.model_rebuild()
PlanRequest.model_rebuild()
MyFitnessPalSyncRequest.model_rebuild()


products: dict[str, Product] = {
    "PRD-OAT": Product(
        product_id="PRD-OAT",
        name="Oatmeal",
        kcal_per_100g=352,
        protein_per_100g=12,
        fat_per_100g=6,
        carbs_per_100g=61,
    ),
    "PRD-CHICK": Product(
        product_id="PRD-CHICK",
        name="Chicken Breast",
        kcal_per_100g=165,
        protein_per_100g=31,
        fat_per_100g=3.6,
        carbs_per_100g=0,
    ),
    "PRD-RICE": Product(
        product_id="PRD-RICE",
        name="Brown Rice",
        kcal_per_100g=112,
        protein_per_100g=2.6,
        fat_per_100g=0.9,
        carbs_per_100g=23,
    ),
    "PRD-SALMON": Product(
        product_id="PRD-SALMON",
        name="Salmon",
        kcal_per_100g=208,
        protein_per_100g=20,
        fat_per_100g=13,
        carbs_per_100g=0,
    ),
    "PRD-BANANA": Product(
        product_id="PRD-BANANA",
        name="Banana",
        kcal_per_100g=89,
        protein_per_100g=1.1,
        fat_per_100g=0.3,
        carbs_per_100g=23,
    ),
}

meal_history: dict[str, list[dict[str, Any]]] = {"USR-DEMO": []}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/products")
async def list_products(search: str | None = None) -> dict[str, Any]:
    items = []
    for product in products.values():
        if search and search.lower() not in product.name.lower():
            continue
        items.append(product.model_dump(mode="json"))
    return {"items": items, "count": len(items)}


@app.post("/nutrition/calculate")
async def calculate_nutrition(request: MealCalculationRequest) -> dict[str, Any]:
    totals = calculate_meal_totals(request.items, products)
    result = {
        "meal_name": request.meal_name,
        "totals": totals.model_dump(mode="json"),
        "calorie_accuracy_tolerance_pct": settings.calorie_accuracy_tolerance_pct,
    }
    if request.user_id:
        entry = {
            "meal_name": request.meal_name,
            "items": [item.model_dump() for item in request.items],
            "totals": totals.model_dump(),
            "created_at": datetime.now(UTC).isoformat(),
        }
        meal_history.setdefault(request.user_id, []).append(entry)
    return result


@app.post("/nutrition/plan")
async def plan_nutrition(request: PlanRequest) -> dict[str, Any]:
    allowed = [item for item in products.values() if item.product_id not in set(request.excluded_products)]
    if not allowed:
        raise HTTPException(status_code=400, detail="No products available after exclusions")
    kcal_per_meal = round(request.target_kcal / request.meals_per_day)
    macro_targets = macro_distribution(request.target_kcal)
    plan_items = []
    for idx in range(request.meals_per_day):
        product = allowed[idx % len(allowed)]
        grams = max(80, min(250, round(kcal_per_meal / max(product.kcal_per_100g, 1) * 100)))
        plan_items.append(
            {
                "meal_index": idx + 1,
                "product_id": product.product_id,
                "grams": grams,
                "kcal_estimate": round(product.kcal_per_100g * grams / 100),
            }
        )
    return {
        "user_id": request.user_id,
        "target_kcal": request.target_kcal,
        "macro_targets": macro_targets,
        "plan": plan_items,
    }


@app.get("/nutrition/summary/{user_id}")
async def nutrition_summary(user_id: str) -> dict[str, Any]:
    history = meal_history.get(user_id, [])
    if not history:
        return {"user_id": user_id, "meals": 0, "calories": 0, "protein": 0, "fat": 0, "carbs": 0}
    calories = sum(float(item["totals"]["calories"]) for item in history)
    protein = sum(float(item["totals"]["protein"]) for item in history)
    fat = sum(float(item["totals"]["fat"]) for item in history)
    carbs = sum(float(item["totals"]["carbs"]) for item in history)
    return {
        "user_id": user_id,
        "meals": len(history),
        "calories": round(calories, 2),
        "protein": round(protein, 2),
        "fat": round(fat, 2),
        "carbs": round(carbs, 2),
    }


@app.post("/integrations/myfitnesspal/sync")
async def sync_myfitnesspal(request: MyFitnessPalSyncRequest) -> dict[str, Any]:
    return {
        "status": "synced",
        "provider": "myfitnesspal",
        "user_id": request.user_id,
        "entries": len(request.entries),
        "synced_at": datetime.now(UTC).isoformat(),
    }


@app.get("/export/{user_id}/excel")
async def export_excel(user_id: str) -> dict[str, Any]:
    history = meal_history.get(user_id, [])
    csv_lines = ["meal_name,calories,protein,fat,carbs,created_at"]
    for meal in history:
        totals = meal["totals"]
        csv_lines.append(
            f"{meal['meal_name']},{totals['calories']},{totals['protein']},{totals['fat']},{totals['carbs']},{meal['created_at']}"
        )
    return {"user_id": user_id, "format": "csv-compatible", "content": "\n".join(csv_lines)}


@app.get("/quality/calorie-accuracy")
async def calorie_accuracy(actual_kcal: float = 2000, estimated_kcal: float = 1890) -> dict[str, Any]:
    error_pct = calorie_error_pct(actual_kcal, estimated_kcal)
    return {
        "actual_kcal": actual_kcal,
        "estimated_kcal": estimated_kcal,
        "error_pct": error_pct,
        "target_within_pct": settings.calorie_accuracy_tolerance_pct,
        "is_within_target": error_pct <= settings.calorie_accuracy_tolerance_pct,
    }
