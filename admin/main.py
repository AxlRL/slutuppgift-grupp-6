import firebase_admin
from firebase_admin import credentials, firestore

from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO

cred = credentials.Certificate('static/cred.json')

firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)

drones = set()

@socketio.on('connect')
def connection():
  print("Server received connection from" + request.sid)
  drones.add(request.sid)

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
