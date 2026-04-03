import json
import re
from decimal import Decimal
from urllib import error, parse, request

from django.conf import settings


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
    heuristic_data = estimate_dish_nutrition(name, description)
    usda_data, reason = request_usda_nutrition(name, description)

    if usda_data:
        return merge_usda_with_tags(usda_data, heuristic_data)

    if reason:
        heuristic_data["nutrition_notes"] = (
            f"{heuristic_data['nutrition_notes']} "
            f"Heuristic fallback was used because {reason}."
        )

    return heuristic_data


def request_usda_nutrition(name, description=""):
    api_key = getattr(settings, "USDA_API_KEY", "")
    if not api_key:
        return None, "the USDA API key is not configured"

    query = build_usda_query(name, description)
    url = getattr(settings, "USDA_SEARCH_URL", "https://api.nal.usda.gov/fdc/v1/foods/search")
    url = f"{url}?api_key={parse.quote(api_key)}"

    data = {
        "query": query,
        "pageSize": 5,
    }

    req = request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=20) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as e:
        return None, f"the USDA request failed with HTTP {e.code}"
    except error.URLError:
        return None, "the USDA service could not be reached"
    except (OSError, ValueError):
        return None, "the USDA request could not be completed"

    foods = response_data.get("foods", [])
    if not foods:
        return None, "USDA did not find a matching food entry"

    food = foods[0]
    calories = extract_usda_calories(food)
    if calories is None:
        return None, "USDA did not return calorie data for the matched food"

    food_name = food.get("description", query)
    return {
        "estimated_calories": calories,
        "nutrition_notes": f"USDA FoodData Central match: {food_name}.",
    }, None


def build_usda_query(name, description=""):
    text = f"{name} {description}".lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = [word for word in text.split() if len(word) > 2]

    if not words:
        return name.strip() or "food"

    return " ".join(dict.fromkeys(words[:6]))


def extract_usda_calories(food):
    for nutrient in food.get("foodNutrients", []):
        nutrient_name = str(nutrient.get("nutrientName", "")).lower()
        unit_name = str(nutrient.get("unitName", "")).lower()
        nutrient_number = str(nutrient.get("nutrientNumber", ""))
        value = nutrient.get("value")

        if value is None:
            continue

        if nutrient_name == "energy" and unit_name == "kcal":
            return int(round(float(value)))

        if nutrient_number in {"1008", "1007", "208"}:
            return int(round(float(value)))

    return None


def merge_usda_with_tags(usda_data, heuristic_data):
    calories = max(usda_data["estimated_calories"], 120)
    is_low_calorie = calories <= 250 or heuristic_data["is_low_calorie"]
    health_score = calculate_health_score(
        calories,
        heuristic_data["is_high_protein"],
        is_low_calorie,
        heuristic_data["is_keto"],
    )

    return {
        "estimated_calories": calories,
        "health_score": health_score,
        "is_veg": heuristic_data["is_veg"],
        "is_keto": heuristic_data["is_keto"],
        "is_high_protein": heuristic_data["is_high_protein"],
        "is_low_calorie": is_low_calorie,
        "nutrition_notes": usda_data["nutrition_notes"],
    }


def calculate_health_score(calories, is_high_protein, is_low_calorie, is_keto):
    health_score = Decimal("5.0")

    if calories <= 250:
        health_score += Decimal("1.2")
    elif calories <= 400:
        health_score += Decimal("0.4")
    elif calories >= 550:
        health_score -= Decimal("1.0")

    if is_high_protein:
        health_score += Decimal("0.8")

    if is_low_calorie:
        health_score += Decimal("0.4")

    if is_keto:
        health_score += Decimal("0.2")

    return min(max(health_score, Decimal("1.0")), Decimal("9.8")).quantize(Decimal("0.1"))
