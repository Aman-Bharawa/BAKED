from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

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

    @override_settings(USDA_API_KEY="test-key")
    @patch("dishes.services.request_usda_nutrition", return_value=(None, "the USDA service could not be reached"))
    def test_usda_fallback_uses_heuristic_when_api_unavailable(self, mocked_request):
        nutrition = estimate_dish_nutrition_with_fallback(
            "Grilled Paneer Bowl",
            "Paneer with vegetables",
        )

        self.assertTrue(mocked_request.called)
        self.assertIn("Heuristic fallback was used because the USDA service could not be reached", nutrition["nutrition_notes"])
        self.assertTrue(nutrition["is_veg"])

    @patch(
        "dishes.services.request_usda_nutrition",
        return_value=(
            {
                "estimated_calories": 310,
                "nutrition_notes": "USDA FoodData Central match: paneer dish.",
            },
            None,
        ),
    )
    def test_usda_result_is_used_when_available(self, mocked_request):
        nutrition = estimate_dish_nutrition_with_fallback(
            "Paneer Bowl",
            "Fresh paneer bowl",
        )

        self.assertTrue(mocked_request.called)
        self.assertEqual(nutrition["estimated_calories"], 310)
        self.assertEqual(nutrition["nutrition_notes"], "USDA FoodData Central match: paneer dish.")
        self.assertEqual(nutrition["health_score"], Decimal("5.4"))
