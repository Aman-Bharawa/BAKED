from django.test import TestCase

from .services import estimate_dish_nutrition, estimate_dish_nutrition_with_fallback


class NutritionServiceTests(TestCase):
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

    def test_fallback_function_returns_heuristic_values(self):
        nutrition = estimate_dish_nutrition_with_fallback(
            "Paneer Bowl",
            "Fresh paneer bowl",
        )

        self.assertEqual(nutrition["estimated_calories"], 260)
        self.assertEqual(str(nutrition["health_score"]), "5.8")
        self.assertIn("Paneer boosts protein", nutrition["nutrition_notes"])
