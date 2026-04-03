# BAKED(Society Homechef MVP)

It is a Django Based MVP of Society Home-chef -- hyperlocal food ordering platform built for gated communities. There are three roles in this platform:

1) "HomeChef" -- publishes dish of the day.
2) "Resident" -- browses dishes and order them.
3) "Rider" -- delivers the food.
4) "Admin" -- controls overall platform

## Tech stack 

 - frontend -- Django templates
 - Backend -- Django
 - Database -- SQLite3
 - Auth -- custom JWT cookie authentication
 - AI nutrition --USDA Fooddata central for nutrition lookup with a local heuristic fallback


## Main Features 

 - custom signin and login for Homechef, Resident, Rider
 - Admin can only login from frontend, to create a new Admin account terminal will be used
 - custom JWT stored in an 'HttpOnly' cookie 
 - Homechef publish dish with:
	- dish name
	- description
	- Meal slot
	- Price
	- Quantity available
	- Image or short video
	- Publish now button
 - automatically generated nutrition fields:
        - calories
	- health scores
	- tags: veg, keto, high protein, low calorie
 - add to cart option
 - only supports cash on delivery
 - inventory auto-decrement when orders are placed by resident
 - riders get orders based on distance from the homechef (distance <= 2km)
 - one rider can only handle one order at a time
 - if rider is free to accept orders then rider able to accept the order
 - rider can set their status of availability
 - website have a feature of notification 


## Nutrition Logic:

1. system first try for USDA FoodData central
2. if USDA is unavailable or does not return a useful match, then system fall back to the 
   local heuristics estimator

The heuristic logic still used for app-specific tags and scoring.

## Local setup
 - change directory to the project directory
 - then open terminal
 - pip install -r requirements.txt
 - python manage.py migrate
 - python manage.py runserver
 - and open 'http://127.0.0.1:8000/'

## Optional USDA API Setup

The app works without a USDA key because it falls back to the heuristic estimator.

To use your own USDA key:

```powershell
$env:USDA_API_KEY="your_usda_key"
python manage.py runserver
```

You can request a key here:

- `https://fdc.nal.usda.gov/api-key-signup.html`

## Admin Account

Admin signup is disabled on the public signup page.

To create an admin account:

```powershell
python manage.py createsuperuser
```

Then log in at:

- `/admin/`
- or the frontend login page

## Main Flows

### HomeChef

1. login as Homechef
2. open `/chef/dishes/`
3. create a dish by filling necessary details
4. upload image or video
5. publish it
6. view calories, health score, tags, and nutrition note

### Resident

1. login as resident
2. open `/resident/feed/`
3. browse dishes from all locations
4. add items to cart
5. open checkout
6. place final order using COD
7. track current and past orders

### Rider

1. login as rider
2. open `/rider/jobs/`
3. go online (or offline)
4. see assigned jobs or nearby open jobs within `2 km`
5. claim or accept a job
6. mark it picked up
7. mark it delivered

## Important Business Rules

- residents can see dishes from every location
- residents can order dishes from every location
- rider matching is based only on distance from the HomeChef's location
- only riders within 2 km are considered for the assignment of order
- one rider can have only one active order at a time
- quantity is reduced when an order is placed
- if quantity of a dish becomes 0, the dish is marked sold out

## Assumptions

- coordinates are mock values entered during signup
- distance is an approximate calculation which is suitable for an MVP
- `location_name` represents the broader delivery area
- HomeChefs and residents are usually inside the main area, while riders may be inside or outside it
- notifications are in-app, not real device push notifications

## if Extended Further

- add feature of modify order from cart 
- add multiple payment options for resident
- subscription service for regular customer
- analytics page for chef where chef can see orders, revenue etc.
- add a better method for AI nutrition estimation.  
