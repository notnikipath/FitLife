from __future__ import annotations

from .schemas import GoalProfile, MealItem, MealTotals, Product


def calculate_meal_totals(items: list[MealItem], products: dict[str, Product]) -> MealTotals:
    calories = protein = fat = carbs = 0.0
    for item in items:
        product = products.get(item.product_id)
        if product is None:
            continue
        ratio = item.grams / 100
        calories += product.kcal_per_100g * ratio
        protein += product.protein_per_100g * ratio
        fat += product.fat_per_100g * ratio
        carbs += product.carbs_per_100g * ratio
    return MealTotals(
        calories=round(calories, 2),
        protein=round(protein, 2),
        fat=round(fat, 2),
        carbs=round(carbs, 2),
    )


def recommended_kcal(weight_kg: float, goal: GoalProfile) -> int:
    base = weight_kg * 30
    if goal.target_weight_kg < weight_kg:
        base -= 350
    elif goal.target_weight_kg > weight_kg:
        base += 250
    base += goal.training_days_per_week * 45
    return max(1200, round(base))


def macro_distribution(target_kcal: int) -> dict[str, int]:
    protein_kcal = target_kcal * 0.3
    fat_kcal = target_kcal * 0.25
    carb_kcal = target_kcal * 0.45
    return {
        "protein_g": round(protein_kcal / 4),
        "fat_g": round(fat_kcal / 9),
        "carbs_g": round(carb_kcal / 4),
    }


def calorie_error_pct(actual_kcal: float, estimated_kcal: float) -> float:
    if actual_kcal <= 0:
        return 0.0
    return round(abs(actual_kcal - estimated_kcal) / actual_kcal * 100, 2)
