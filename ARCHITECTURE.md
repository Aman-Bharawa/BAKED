# Architecture Note

## Project Shape

This project is a single Django application with server-rendered templates and there are three main domain apps:

- `accounts`
- `dishes`
- `orders`

This keeps the project simple, readable, and easy to demo end to end from one codebase.

## Why Django

Django was a good choice here because the assignment needed:

- authentication
- role-based flows
- file uploads
- database models
- admin access
- fast delivery of an end-to-end product

The frontend complexity is reduced by using Django templates and it becomes easier to make the working project in less time.

## App Responsibilities

### `accounts`

Handles:

- custom user model
- roles: admin, chef, resident, rider
- signup and login forms
- custom JWT cookie auth
- dashboard rendering

### `dishes`

Handles:

- dish model
- chef publishing flow
- meal slots
- media upload
- AI-nutrition generation
- sold-out handling

### `orders`

Handles:

- resident cart and checkout
- order creation
- rider assignment
- rider claim flow
- delivery status updates
- notifications

## Core Models

### User

Stores:

- email
- role
- location name
- phone number
- rider vehicle details
- latitude and longitude
- rider availability

### Dish

Stores:

- chef
- dish details
- media
- meal slot
- quantity
- publish state
- nutrition values
- tags

### Order

Stores:

- resident
- chef
- dish
- rider
- quantity
- total price
- current status

### Notification

Stores:

- recipient
- title
- message
- related order

## Authentication Design

custom JWT flow instead of Django session login for main frontend in this app.

Flow:

1. first user signs up or logs in
2. then backend validates the credentials
3. backend generates a JWT
4. token is stored in an `HttpOnly` cookie
5. middleware then reads the cookie and attaches the user to the request

here django admin still uses Django’s normal staff/superuser mechanism.

## Nutrition Design

The project uses a local heuristic nutrition pipeline.

When a HomeChef creates a dish, the backend reads the dish name and description and evaluates food-related keywords. It first checks for a base dish type such as `paratha`, `rice`, `wrap`, `salad`, or `dessert` and assigns a starting calorie estimate. After that, it looks for ingredient and cooking-method keywords such as `paneer`, `chicken`, `egg`, `dal`, `fried`, `grilled`, `boiled`, `butter`, `cream`, `ghee`, `keto`, and `avocado`.

Using these detected keywords, the system calculates:
- estimated calories
- health score
- veg tag
- keto tag
- high protein tag
- low calorie tag

The result is saved directly on the dish record along with a short `nutrition_notes` explanation, so the resident and chef interfaces can display the reasoning clearly.

This design was chosen because it is simple, deterministic, explainable, and does not depend on any external API . Although it is not nutritionally exact, but it works well for an MVP

## Ordering Design

Within the society residents can browse all live dishes 

The resident flow is:

1. browse dishes
2. add items to cart
3. open checkout
4. place final order with COD

After placing the order, the inventory for that dish get auto-decrement

## Rider Design

Distance-based approach is used for rider.

Rules:

- to accpet the order riders must be online
- riders can only have one active order at a time
- assigned jobs and nearby open jobs are shown on the rider page
- nearby means `<= 2 km` from the HomeChef pickup point

If no rider is auto-assigned, a free nearby rider can still claim the open job.

## Distance Logic

Distance is calculated using a lightweight approximation based on latitude and longitude differences.
because the project is an MVP

## Scale Limitations

Current limitations if scaled heavily:

- SQLite is not ideal for concurrent writes
- rider assignment runs synchronously during request handling
- notifications are stored and shown in-app only
- only have COD as a payment mode
- Feedback option is not available

## Future Direction

Natural next upgrades would be:

- PostgreSQL
- built a better cart controls
- add multiple payment options for resident
- subscription service for regular customer
- analytics page for chef where chef can see orders, revenue etc.
- add a better method for AI nutrition estimation.  
