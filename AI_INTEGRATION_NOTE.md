# AI Integration Note

## Current Approach

The project uses:

1. USDA FoodData Central as the primary nutrition source
2. a local heuristic pipeline as the fallback

It doesn't depend on paid AI. 
This keeps the system more practical for an assignment project while still showing a thoughtful nutrition pipeline.


## Why This Approach Was Chosen

since the assignment values pipeline design and implementation thinking more than perfect nutritional accuracy.

This design works well because:

- it does not depend fully on a paid external AI service
- it still uses a real data source when available
- it always returns a usable result through fallback
- it is easy to explain in a debrief

## Pipeline Flow

### Step 1

Read the dish name and description.

### Step 2

Build a USDA search query from the important words in the dish text.

### Step 3

then calls USDA FoodData Central `foods/search`.

### Step 4

If USDA returns a matching food with calorie information then use USDA calories and create a nutrition note using the matched USDA description

### Step 5

Use local app logic to derive:

- health score
- veg tag
- keto tag
- high protein tag
- low calorie tag

### Step 6

If USDA does not return a useful result then  fall back to the local heuristic estimator and store the fallback reason in the nutrition note

## What USDA Provides

USDA can provide:

- food match description
- calories
- other nutrient data (if extended further)

USDA does not provide:

- a direct health score
- project-specific dietary tags
- a resident-facing explanation in your product language

That is the reason the app still computes health score and tags locally.

## Heuristic Fallback

The local heuristic estimator uses dish keywords such as:

- `paneer`
- `chicken`
- `egg`
- `dal`
- `fried`
- `grilled`
- `boiled`
- `butter`
- `cream`
- `ghee`
- `keto`
- `avocado`

It also checks for base dish types such as:

- `paratha`
- `rice`
- `salad`
- `wrap`
- `burger`
- `dessert`

From these signals it estimates:

- calories
- health score
- veg
- keto
- high protein
- low calorie

## Example Output

Possible resident-side output:

- `Calories: 310 kcal`
- `Health Score: 5.4 / 10`
- `Nutrition Source: USDA FoodData Central`
- `Nutrition Note: USDA FoodData Central match: Paneer dish.`

If fallback is used:

- `Nutrition Source: Heuristic`
- `Nutrition Note: ... Heuristic fallback was used because USDA did not find a matching food entry.`

## Benefits

- works with or without USDA configuration
- always produces visible nutrition metadata
- easy to explain to reviewers
- avoids hard dependency on a single external service

## Limitations

- USDA search is still text-based, not true dish understanding
- dish descriptions may not always match a USDA food cleanly
- health score is app-defined, not medically validated
- tags are logic-based approximations, not clinical nutrition labels

## If Extended Further

The next improvement would be to use more USDA nutrient values such as:

- protein
- sugar
- fat
- sodium
- fiber

That would allow the health score to be based on more than calories plus keyword-based tags.
