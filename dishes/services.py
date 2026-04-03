import re
from decimal import Decimal


BASE_CALORIES = {
    "paratha": 250,
    "rice": 220,
    "biryani": 420,
    "curry": 280,
    "salad": 140,
    "wrap": 260,
    "sandwich": 240,
    "soup": 150,
    "pizza": 320,
    "burger": 340,
    "dessert": 360,
    "cake": 340,
    "halwa": 320,
    "noodles": 300,
    "pasta": 310,
}

KEYWORD_RULES = {
    "paneer": {"calories": 80, "health": 0.8, "protein": 2, "veg": True, "note": "Paneer boosts protein but adds fat."},
    "chicken": {"calories": 90, "health": 1.0, "protein": 3, "note": "Chicken improves protein density."},
    "egg": {"calories": 70, "health": 0.8, "protein": 2, "note": "Egg adds balanced protein."},
    "dal": {"calories": 60, "health": 1.2, "protein": 2, "veg": True, "note": "Dal supports fiber and protein."},
    "salad": {"calories": -20, "health": 1.8, "veg": True, "low_calorie": True, "note": "Salad usually means a lighter dish."},
    "grilled": {"calories": -30, "health": 1.6, "low_calorie": True, "note": "Grilled dishes are usually lighter than fried ones."},
    "boiled": {"calories": -40, "health": 1.4, "low_calorie": True, "note": "Boiled preparation reduces added fat."},
    "fried": {"calories": 110, "health": -2.2, "note": "Fried food raises oil and calorie load."},
    "butter": {"calories": 90, "health": -1.4, "veg": True, "note": "Butter adds richness but lowers the health score."},
    "cream": {"calories": 80, "health": -1.2, "veg": True, "note": "Cream makes the dish heavier."},
    "ghee": {"calories": 70, "health": -1.0, "veg": True, "note": "Ghee increases calorie density."},
    "mayo": {"calories": 90, "health": -1.8, "note": "Mayo increases fat content."},
    "keto": {"calories": 20, "health": 0.6, "keto": True, "note": "Keto-style dish hints at lower carb content."},
    "avocado": {"calories": 40, "health": 0.7, "keto": True, "note": "Avocado often fits keto-style meals."},
    "cauliflower rice": {"calories": -40, "health": 0.9, "keto": True, "low_calorie": True, "note": "Cauliflower rice usually points to a lower-carb dish."},
    "vegan": {"calories": -10, "health": 1.0, "veg": True, "note": "Vegan dishes tend to be lighter."},
}


def estimate_dish_nutrition(name, description=""):
    text = f"{name} {description}".lower()
    calories = 180
    health_score = Decimal("5.0")
    protein_points = 0
    is_veg = True
    is_keto = False
    notes = []
    low_calorie_match = False

    for word, value in BASE_CALORIES.items():
        if re.search(rf"\b{re.escape(word)}\b", text):
            calories = value
            notes.append(f"Base calories set from '{word}'.")
            break

    for word, values in KEYWORD_RULES.items():
        if re.search(rf"\b{re.escape(word)}\b", text):
            calories += values.get("calories", 0)
            health_score += Decimal(str(values.get("health", 0)))
            protein_points += values.get("protein", 0)
            low_calorie_match = low_calorie_match or values.get("low_calorie", False)
            is_keto = is_keto or values.get("keto", False)

            if "veg" in values:
                is_veg = values["veg"]
            else:
                is_veg = is_veg and word not in {"chicken", "egg"}

            note = values.get("note")
            if note:
                notes.append(note)

    if calories < 120:
        calories = 120

    is_high_protein = protein_points >= 3
    is_low_calorie = calories <= 250 or low_calorie_match

    if is_high_protein:
        notes.append("Protein-heavy ingredients improved the final rating.")
        health_score += Decimal("0.4")

    if is_low_calorie:
        notes.append("The total calorie estimate stayed in the lighter range.")
        health_score += Decimal("0.3")

    sweets = ("dessert", "cake", "halwa")
    if any(re.search(rf"\b{re.escape(word)}\b", text) for word in sweets):
        is_veg = True
        health_score -= Decimal("0.8")
        notes.append("Dessert-style dishes usually have more sugar.")

    health_score = min(max(health_score, Decimal("1.0")), Decimal("9.8"))

    return {
        "estimated_calories": calories,
        "health_score": health_score.quantize(Decimal("0.1")),
        "is_veg": is_veg,
        "is_keto": is_keto,
        "is_high_protein": is_high_protein,
        "is_low_calorie": is_low_calorie,
        "nutrition_notes": " ".join(dict.fromkeys(notes)) or "Heuristic estimate generated from dish name and description.",
    }


def estimate_dish_nutrition_with_fallback(name, description="", media=None):
    return estimate_dish_nutrition(name, description)
