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

INGREDIENT_PROFILES = {
    "paneer": {
        "calories_per_unit": Decimal("2.67"),
        "default_units": 30,
        "units_by_base": {"wrap": 35, "sandwich": 30, "curry": 55, "pizza": 45, "burger": 35},
        "health": 0.8,
        "protein": 2,
        "veg": True,
        "note": "Paneer boosts protein but adds fat.",
    },
    "chicken": {
        "calories_per_unit": Decimal("1.9"),
        "default_units": 70,
        "units_by_base": {"sandwich": 55, "wrap": 60, "burger": 65, "salad": 60, "curry": 105, "biryani": 95, "pizza": 70, "pasta": 80, "noodles": 80},
        "health": 1.0,
        "protein": 3,
        "note": "Chicken improves protein density.",
    },
    "egg": {
        "calories_per_unit": Decimal("1.55"),
        "default_units": 45,
        "units_by_base": {"sandwich": 40, "wrap": 45, "burger": 50, "salad": 35, "curry": 60},
        "health": 0.8,
        "protein": 2,
        "note": "Egg adds balanced protein.",
    },
    "dal": {
        "calories_per_unit": Decimal("1.1"),
        "default_units": 55,
        "units_by_base": {"soup": 70, "curry": 80, "rice": 45},
        "health": 1.2,
        "protein": 2,
        "veg": True,
        "note": "Dal supports fiber and protein.",
    },
}

KEYWORD_RULES = {
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


def extract_main_ingredient(description):
    if not description:
        return ""

    match = re.search(
        r"main ingredient\s*:\s*([a-zA-Z][a-zA-Z\s]{1,40})",
        description,
        re.IGNORECASE,
    )
    if not match:
        return ""

    ingredient_name = match.group(1).strip().lower()
    ingredient_name = re.split(r"[.,;\n]", ingredient_name)[0].strip()
    return ingredient_name


def detect_base_item(text):
    for word, value in BASE_CALORIES.items():
        if re.search(rf"\b{re.escape(word)}\b", text):
            return word, value
    return None, 180


def calculate_ingredient_calories(word, values, base_item, text, main_ingredient_amount=None):
    units = values.get("default_units", 0)

    if base_item:
        units = values.get("units_by_base", {}).get(base_item, units)

    if main_ingredient_amount:
        units = int(main_ingredient_amount)

    if re.search(r"\bmini\b|\bsmall\b", text):
        units = int(units * 0.8)

    if re.search(r"\blarge\b|\bloaded\b|\bfull\b", text):
        units = int(units * 1.25)

    calories = int((values["calories_per_unit"] * Decimal(str(units))).quantize(Decimal("1")))
    return calories, units


def estimate_dish_nutrition(name, description="", main_ingredient_amount=None):
    main_ingredient_name = extract_main_ingredient(description)
    text = f"{name} {description}".lower()
    if main_ingredient_name and not re.search(rf"\b{re.escape(main_ingredient_name)}\b", text):
        text = f"{text} {main_ingredient_name}"

    base_item, calories = detect_base_item(text)
    health_score = Decimal("5.0")
    protein_points = 0
    is_veg = True
    is_keto = False
    notes = []
    low_calorie_match = False

    if base_item:
        notes.append(f"Base calories set from '{base_item}'.")

    if main_ingredient_name:
        notes.append(f"Main ingredient taken from description: {main_ingredient_name}.")

    for word, values in INGREDIENT_PROFILES.items():
        if re.search(rf"\b{re.escape(word)}\b", text):
            ingredient_calories, estimated_units = calculate_ingredient_calories(
                word,
                values,
                base_item,
                text,
                main_ingredient_amount,
            )
            calories += ingredient_calories
            health_score += Decimal(str(values.get("health", 0)))
            protein_points += values.get("protein", 0)

            if "veg" in values:
                is_veg = values["veg"]
            else:
                is_veg = is_veg and word not in {"chicken", "egg"}

            note = values.get("note")
            if note:
                notes.append(note)
            if main_ingredient_amount:
                notes.append(f"{word.title()} amount used from chef input: about {estimated_units} g/ml.")
            else:
                notes.append(f"{word.title()} portion estimated around {estimated_units} g/ml for this dish style.")

    for word, values in KEYWORD_RULES.items():
        if re.search(rf"\b{re.escape(word)}\b", text):
            calories += values.get("calories", 0)
            health_score += Decimal(str(values.get("health", 0)))
            protein_points += values.get("protein", 0)
            low_calorie_match = low_calorie_match or values.get("low_calorie", False)
            is_keto = is_keto or values.get("keto", False)

            if "veg" in values:
                is_veg = values["veg"]

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


def estimate_dish_nutrition_with_fallback(name, description="", media=None, main_ingredient_amount=None):
    return estimate_dish_nutrition(name, description, main_ingredient_amount)
