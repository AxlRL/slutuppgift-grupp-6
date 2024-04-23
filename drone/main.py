import argparse
import math
import json
import socketio

current_coords = None

sio = socketio.Client()

@sio.event
def on_message(message):
    global current_coords

    message = json.loads(message)

    if message['type'] == 'order':
        fly_to_order(message['order'])

def fly_to_order(order):
    fly_to_coords(order['from'])

    wait_for_confirmation()

    fly_to_coords(order['to'])

    wait_for_confirmation()

    sio.send({
        'type': 'order_completed',
        'order_id': order['id']
    })

def fly_to_coords(coords):
    global current_coords

    while distance(current_coords, coords) > 0.0002:
        d_lon, d_lat = current_coords[0] - coords[0], current_coords[1] - coords[1]

        current_coords = (current_coords[0] + d_lon, current_coords[1] + d_lat)

        send_location()

def wait_for_confirmation():
    pass

def distance(pos_a, pos_b):
    return math.sqrt((pos_a[0] - pos_b[0])**2 + (pos_a[1] - pos_b[1])**2)

def send_location():
    global sio, current_coords

    sio.send({
        'type': 'location',
        'id': drone_id,
        'coords': current_coords
    })

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
