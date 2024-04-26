import argparse
import math
import json
import socketio
import time

current_coords = None

sio = socketio.Client()

@sio.on('message')
def on_message(message):
    time.sleep(1)
    global current_coords

    message = json.loads(message)
    print("Received message: " + str(message))

    if message['type'] == 'order':
        fly_to_order(message)

def fly_to_order(order):
    fly_to_coords(order['from'])

    wait_for_confirmation()

    fly_to_coords(order['to'])

    wait_for_confirmation()

    print("Arrived at:" + str(current_coords))
    sio.emit("order_completed", "Order completed, at " + str(current_coords))

def fly_to_coords(coords):
    global current_coords
    coords = (float(coords[0]), float(coords[1]))
    speed = 0.0001

    while distance(current_coords, coords) > 0.0002:
        d_lat, d_lon = (coords[0] - current_coords[0], coords[1] - current_coords[1])

        current_coords = (current_coords[0] + d_lat*speed, current_coords[1] + d_lon*speed)

        send_location()

def wait_for_confirmation():
    pass

def distance(pos_a, pos_b):
    dist = math.sqrt((pos_a[0] - pos_b[0])**2 + (pos_a[1] - pos_b[1])**2)
    print(dist)
    return dist

def send_location():
    global sio, current_coords

    jsonCoords = json.dumps({"Lon": current_coords[0], "Lat": current_coords[1]})

    sio.emit("location", jsonCoords)

if __name__ == "__main__":
    ## Parse Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", help = 'Drone ID', type=str, required=True)
    parser.add_argument("--current_lat", help ='Current Drone Latitude', type=float, default=55.7076368)
    parser.add_argument("--current_lon", help ='Current Drone Longitude', type=float, default=13.1880542)
    args = parser.parse_args()

    drone_id = args.id
    current_coords = (args.current_lon, args.current_lat)

    ## Connect To Command Server
    sio.connect("http://localhost:8080")
    sio.wait()

