# AI Integration Note

## Current Approach

The project uses only a local heuristic nutrition pipeline.

It does not depend on any paid AI service or external nutrition API.
This keeps the system more practical for the assignment and also makes the app reliable because nutrition estimation works every time without internet or API key dependency.

## Why This Approach Was Chosen

since the assignment values pipeline design and implementation thinking more than perfect nutritional accuracy.

This design works well because:

- it does not depend on any paid external AI service
- it does not depend on any external nutrition API
- it always returns a usable result
- it is simple to explain in a debrief
- it is easy to maintain in a local MVP

## Pipeline Flow

### Step 1

Read the dish name and description.

### Step 2

Check for a base dish type from the dish text such as `paratha`, `rice`, `wrap`, `salad`, `burger`, or `dessert`.

### Step 3

Assign a base calorie estimate from that detected dish type.

### Step 4

Check for ingredient and cooking-method keywords such as `paneer`, `chicken`, `egg`, `dal`, `fried`, `grilled`, `boiled`, `butter`, `cream`, `ghee`, `keto`, and `avocado`.

### Step 5

Adjust calories and health score based on those detected keywords.

### Step 6

Use local app logic to derive:

- health score
- veg tag
- keto tag
- high protein tag
- low calorie tag

### Step 7

Save the final nutrition note along with calories, score, and tags in the dish record.

## What Heuristic Logic Provides

The heuristic pipeline provides:

- estimated calories
- health score
- nutrition note
- veg tag
- keto tag
- high protein tag
- low calorie tag

It does not provide:

- exact nutritional accuracy
- real ingredient weight analysis
- lab-tested nutrition values
- image-based food understanding

That is okay for this project because the goal is to show a clear and working nutrition estimation pipeline.

## Heuristic Logic

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
- `Health Score: 5.8 / 10`
- `Nutrition Source: Heuristic`
- `Nutrition Note: Base calories set from 'wrap'. Paneer boosts protein but adds fat. Grilled dishes are usually lighter than fried ones.`

## Benefits

- always works without any external dependency
- always produces visible nutrition metadata
- easy to explain to reviewers
- simple and deterministic
- suitable for an MVP

## Limitations

- it is text-based, not image-based
- dish descriptions may not always contain enough useful keywords
- health score is app-defined, not medically validated
- tags are logic-based approximations, not clinical nutrition labels

## If Extended Further

The next improvement would be:

- use dish image understanding
- use more detailed ingredient-level nutrition logic
- separate confidence score from health score
- improve calorie estimation using quantity and portion size
