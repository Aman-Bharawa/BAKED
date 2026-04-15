from django.test import TestCase

from .services import (
    estimate_dish_nutrition,
    estimate_dish_nutrition_with_fallback,
    extract_main_ingredient,
)


class NutritionServiceTests(TestCase):
    def test_main_ingredient_can_be_extracted_from_description(self):
        ingredient_name = extract_main_ingredient(
            "Main ingredient: chicken. Rich gravy with mild spice."
        )

        self.assertEqual(ingredient_name, "chicken")

    def test_keto_keyword_sets_keto_tag(self):
        nutrition = estimate_dish_nutrition(
            "Keto Paneer Bowl",
            "Low carb keto paneer meal with avocado",
        )

        self.assertTrue(nutrition["is_keto"])
        self.assertTrue(nutrition["is_veg"])

    def test_word_matching_does_not_mistake_veggies_for_egg(self):
        nutrition = estimate_dish_nutrition(
            "Paneer Grilled Wrap",
            "High protein grilled paneer wrap with light veggies",
        )

        self.assertTrue(nutrition["is_veg"])

    def test_portion_aware_heuristic_differentiates_chicken_dishes(self):
        sandwich = estimate_dish_nutrition(
            "Chicken Sandwich",
            "Light grilled chicken sandwich",
        )
        butter_chicken = estimate_dish_nutrition(
            "Butter Chicken",
            "Rich butter chicken curry",
        )

        self.assertGreater(butter_chicken["estimated_calories"], sandwich["estimated_calories"])
        self.assertIn("Chicken portion estimated", butter_chicken["nutrition_notes"])

    def test_chef_entered_main_ingredient_amount_changes_estimate(self):
        default_estimate = estimate_dish_nutrition(
            "Chicken Sandwich",
            "Light grilled chicken sandwich",
        )
        custom_estimate = estimate_dish_nutrition(
            "Chicken Sandwich",
            "Light grilled chicken sandwich",
            main_ingredient_amount=120,
        )

        self.assertGreater(custom_estimate["estimated_calories"], default_estimate["estimated_calories"])
        self.assertIn("chef input", custom_estimate["nutrition_notes"])

    def test_description_main_ingredient_affects_estimate(self):
        nutrition = estimate_dish_nutrition(
            "Classic Sandwich",
            "Main ingredient: chicken. Light grilled filling.",
            main_ingredient_amount=100,
        )

        self.assertFalse(nutrition["is_veg"])
        self.assertIn("Main ingredient taken from description", nutrition["nutrition_notes"])

    def test_fallback_function_returns_heuristic_values(self):
        nutrition = estimate_dish_nutrition_with_fallback(
            "Paneer Bowl",
            "Fresh paneer bowl",
        )

        self.assertEqual(nutrition["estimated_calories"], 260)
        self.assertEqual(str(nutrition["health_score"]), "5.8")
        self.assertIn("Paneer boosts protein", nutrition["nutrition_notes"])
