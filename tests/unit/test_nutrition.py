from shared.fitlife_common import calculate_meal_totals, calorie_error_pct, macro_distribution
from shared.fitlife_common.schemas import MealItem, Product


def test_meal_totals() -> None:
    products = {
        "A": Product(
            product_id="A",
            name="Oats",
            kcal_per_100g=350,
            protein_per_100g=12,
            fat_per_100g=6,
            carbs_per_100g=60,
        ),
    }
    totals = calculate_meal_totals([MealItem(product_id="A", grams=50)], products)
    assert totals.calories > 0
    assert totals.carbs > 0


def test_macro_distribution() -> None:
    macros = macro_distribution(2400)
    assert macros["protein_g"] > 0
    assert macros["fat_g"] > 0
    assert macros["carbs_g"] > 0


def test_calorie_error_pct() -> None:
    value = calorie_error_pct(2000, 1900)
    assert value == 5.0
