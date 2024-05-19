from flask import Flask, request
from flask_socketio import SocketIO, emit
import asyncio
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Flask and SocketIO
app = Flask(__name__)
sio = SocketIO(app)

# Initialize Firebase
cred = credentials.Certificate('static/sa_credentials.json')  # Replace with your Firebase credentials file
firebase_admin.initialize_app(cred)
db = firestore.client()

# Global dictionaries to store drone and delivery information
connected_drones = {}
delivery_requests = {}
drone_sid_id = {}

# Firestore collection names
DRONES_COLLECTION = 'drones'
DELIVERIES_COLLECTION = 'deliveries'

@sio.event
def connect():
    print('Client connected')

@sio.event
def disconnect():
    print('Client disconnected')

    drone_id = drone_sid_id.get(request.sid)
    if drone_id:
        drone_ref = connected_drones[drone_id]['ref']
        drone_ref.update({'status': 'offline', 'latitude': None, 'longitude': None})
        del connected_drones[drone_id]
        del drone_sid_id[request.sid]
        print(f"Drone {drone_id} disconnected")


@sio.on('drone_handshake')
def handle_handshake(data):
  print('Handling handshake')
  drone_id = data.get('drone_id')
  if drone_id:
      drone_ref = db.collection(DRONES_COLLECTION).document(drone_id)

      if not drone_ref.get().exists:
          print(f"Drone {drone_id} not found in database.")
          return {'success': False}

      drone_ref.update({
          'status': 'idle',
          'latitude': None,
          'longitude': None,
      })

      connected_drones[drone_id] = {'target': None, 'ref': drone_ref, 'sid': request.sid, 'delivery': None}
      drone_sid_id[request.sid] = drone_id

      assign_deliveries()

      return {'success': True, 'drone_id': drone_id}
  else:
      return {'success': False}

@sio.on('drone_location')
def handle_drone_location(data):
    drone_id = data.get('drone_id')
    current_coords = data.get('current_coords')
    if drone_id:
        if drone_id in connected_drones:
            connected_drones[drone_id]['ref'].update({
              'latitude': current_coords[0],
              'longitude': current_coords[1]
            })
            # print(f"Drone {drone_id} location updated in Firestore: {current_coords}")
        else:
            print(f"Unknown drone: {drone_id}")

@sio.on("arrived")
def handle_arrived(data):
    drone_id = data.get('drone_id')
    if not drone_id:
        return

    if not drone_id in connected_drones:
        print(f"Unknown drone: {drone_id}")
        return

    drone_data = connected_drones[drone_id]
    delivery_id = drone_data['delivery']

    if not delivery_id:
        print(f"Drone {drone_id} arrived at unknown location")
        return

    delivery_ref = delivery_requests[delivery_id]['ref']
    delivery_status = delivery_ref.get().to_dict()['status']

    if delivery_status == 'flight_to_pickup':
        delivery_ref.update({'status': 'flight_to_dropoff'})
        print(f"Drone {drone_id} arrived at pickup location for delivery {delivery_id}")
        dropoff_coords = delivery_ref.get().to_dict()['dropoff_coords']
        sio.emit('set_target', {'coords': dropoff_coords}, room=drone_data['sid'])
    elif delivery_status == 'flight_to_dropoff':
        delivery_ref.update({'status': 'completed'})
        drone_data['ref'].update({'status': 'idle', 'delivery_id': None})
        drone_data['delivery'] = None
        print(f"Drone {drone_id} arrived at dropoff location for delivery {delivery_id}")
        assign_deliveries()
    else:
        print(f"Drone {drone_id} arrived at unknown location for delivery {delivery_id}")

@app.route('/request_delivery', methods=['POST'])
def request_delivery():
    data = request.get_json()
    pickup_coords = data.get('pickup_coords')
    dropoff_coords = data.get('dropoff_coords')

    if pickup_coords and dropoff_coords:
        _,delivery_ref = db.collection(DELIVERIES_COLLECTION).add({
            'pickup_coords': pickup_coords,
            'dropoff_coords': dropoff_coords,
            'status': 'pending',
            'company': data.get('company'),
            'created_at': firestore.SERVER_TIMESTAMP,
        })
        # Add delivery request to local dictionary
        delivery_requests[delivery_ref.id] = {'ref': delivery_ref}
        print(f"New delivery request added: {delivery_ref.id}")

        # Attempt to assign the delivery to an available drone
        assign_deliveries()

        return f"Delivery request submitted with ID: {delivery_ref.id}", 200
    else:
        return "Invalid delivery request data", 400


def assign_deliveries():
    for delivery_id, delivery_data in delivery_requests.items():
        if delivery_data['ref'].get().to_dict()['status'] == 'pending':
            for drone_id, drone_data in connected_drones.items():
                if drone_data['ref'].get().to_dict()['status'] == 'idle':
                    # Assign delivery to drone in Firestore
                    delivery_data['ref'].update({'drone_id': drone_id, 'status': 'flight_to_pickup'})
                    # Update drone availability in Firestore
                    drone_data['ref'].update({'status': 'busy', 'delivery_id': delivery_id})
                    drone_data['delivery'] = delivery_id
                    # Send target coordinates to drone
                    pickup_coords = delivery_data['ref'].get().to_dict()['pickup_coords']
                    print(f"Assigning delivery {delivery_id} to drone {drone_id}")
                    sio.emit('set_target', {'coords': pickup_coords}, room=drone_data['sid'])
                    print(f"Delivery {delivery_id} assigned to drone {drone_id}")
                    return

if __name__ == '__main__':
    # mark all old deliveries as completed

    for doc in db.collection(DELIVERIES_COLLECTION).where('status', '!=', 'completed').stream():
        doc.reference.update({'status': 'completed'})
        print(f"Marked old delivery {doc.id} as completed")

    for drone in db.collection(DRONES_COLLECTION).where('status', '!=', 'offline').stream():
        drone.reference.update({'status': 'offline', 'latitude': None, 'longitude': None, 'delivery_id': None})
        print(f"Marked old drone {drone.id} as offline")

    sio.run(app, host='0.0.0.0', port=8080)
