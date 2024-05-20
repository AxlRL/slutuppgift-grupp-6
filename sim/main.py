import time
import random
import requests
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("static/sa_credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Function to pick a random number of deliveries (0 to 3)
def pick_random_deliveries():
    return random.randint(0, 3)

# Function to pick a random wait time (30 to 60 seconds)
def pick_random_wait_time():
    return random.randint(15, 30)

def random_coords():
    return (random.uniform(55.68100271828136, 55.743560192701395), random.uniform(13.144806425692959, 13.252574789032378))

def random_company():
    return random.choice([
      'Fooodz',
      'Groceriez',
      'Deliveroo',
      'Uber Oats',
      'Eatsy',
      'Munchly',
      'NoshDash',
      'ZestyBites',
      'Snackaroo',
      'SwiftGrub',
      'BiteRide',
      'QuickCart',
      'GrabNGo',
      'SpeedyGro',
      'FreshFleet',
      'ChowNow',
      'YummyWay',
      'CraveCabs',
      'FoodSprint',
      'BountyBite',
      'FeastFast',
      'NibbleNest',
      'GrocyGo',
      'RapidEats'
    ])

# Function to request a new delivery
def request_delivery():
    response = requests.post('http://localhost:8080/request_delivery', json= {
      'pickup_coords': random_coords(),
      'dropoff_coords': random_coords(),
      'company': random_company(),
    })
    if response.status_code == 200:
        print("Delivery requested successfully.")
    else:
        print(f"Failed to request delivery: {response.status_code}")

# Main loop
while True:
    try:
        # Pick a random number of deliveries to maintain
        target_deliveries = pick_random_deliveries()

        # Wait for a random amount of time
        wait_time = pick_random_wait_time()
        print(f"Waiting for {wait_time} seconds...")
        time.sleep(wait_time)

        # Get the current number of queued deliveries
        deliveries_ref = db.collection('deliveries').where('status', '==', 'pending')
        current_deliveries = len([doc for doc in deliveries_ref.stream()])

        print(f"Current deliveries: {current_deliveries}, Target deliveries: {target_deliveries}")

        # If current deliveries are less than target, enqueue more deliveries
        if current_deliveries < target_deliveries:
            deliveries_to_add = target_deliveries - current_deliveries
            for _ in range(deliveries_to_add):
                request_delivery()

    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(30)  # Wait before retrying
