import firebase_admin
from firebase_admin import credentials, firestore

from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO
import json
import time

cred = credentials.Certificate('static/cred.json')

firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)

drones_sid_id = {}
drones_id_sid = {}

# Drone Connect
@socketio.on('connect')
def connection():
  print("Connected", request.sid)

# Drone Connection Handshake
@socketio.on("hello")
def drone_hello(data):
  print("Drone hello", data, request.sid)

  drones_id_sid[data["drone_id"]] = request.sid
  drones_sid_id[request.sid] = data["drone_id"]

  db.collection("drones").document(data["drone_id"]).update({
    "status": "online",
  })

# Drone Disconnect
@socketio.on('disconnect')
def disconnection():
  global drones_sid_id, drones_id_sid
  print("Disconnected", request.sid)

  drone_id = drones_sid_id[request.sid]
  db.collection("drones").document(drone_id).update({
    "status": "offline",
  })

  del drones_sid_id[request.sid]
  del drones_id_sid[drone_id]

# Drone Location Update
@socketio.on("drone_location")
def drone_update_location(data):
  print("Drone location", data)

  db.collection("drones").document(data["drone_id"]).update({
    "latitude": data["current_coords"][0],
    "longitude": data["current_coords"][1],
  })

# Drone Arrived At Destination
@socketio.on("arrived")
def drone_arrived(data):
  print("Drone arrived", data)

  drone = db.collection("drones").document(data["drone_id"])
  drone.update({
    "status": "idle",
    "flying_to": None,
  })

@app.route("/drones/<drone_id>/fly-to", methods=["POST"])
def fly_to_endpoint(drone_id):
  global socketio, drones_id_sid
  body = request.get_json()

  print("Fly to", drone_id, body)

  drone = db.collection("drones").document(drone_id)
  drone.update({
    "status": "flying",
    "flying_to": body["to"],
  })

  drone_sid = drones_id_sid[drone_id]

  socketio.emit("fly_to_coordinates", body["to"], to=drone_sid)

  return "OK"

@app.route("/drones", methods=["GET"])
def get_drones_endpoint():
  global drones_id_sid

  return json.dumps(drones_id_sid)

@app.route("/place-order", methods=["POST"])
def place_order_endpoint():
  body = request.get_json()

  order = {
    "status": "pending",
    "from": body["from"],
    "to": body["to"],
  }

  db.collection("orders").add(order)

  return "Order placed"

@app.route("/update-location", methods=["PUT"])
def update_location_endpoint():
  body = request.get_json()

  drone = db.collection("drones").document(body["id"])
  drone.update({
    "longitude": body["longitude"],
    "latitude": body["latitude"],
  })

  return "Location updated"

@app.route("/get-next-order", methods=["POST"])
def get_next_order_endpoint():
  body = request.get_json()

  order = db.collection("orders").where("status", "==", "pending").limit(1).get()

  if len(order) == 0:
    return "No orders available"

  order = order[0]
  order.reference.update({"status": "claimed"})

  return order.to_dict()

if __name__ == "__main__":
  socketio.run(app, debug=True, host='0.0.0.0', port='8080')
