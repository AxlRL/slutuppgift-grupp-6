import argparse


current_coords = (55.7076368, 13.1880542)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", help ='drones ID', type=str, required=True)
    args = parser.parse_args()

    drone_id = args.id

    while True:
        new_order = get_new_order()

        fly_to_order(new_order)

def fly_to_order(order):
    fly_to_coords(order['from'])

    wait_for_confirmation()

    fly_to_coords(order['to'])

def fly_to_coords(coords):
    global current_coords

    while distance(current_coords, coords) > 0.0002:
        move_drone_towards(coords)
        send_location()

def move_drone_towards(coords):
    global current_coords

    d_lon, d_lat = current_coords[0] - coords[0], current_coords[1] - coords[1]

    current_coords = (current_coords[0] + d_lon, current_coords[1] + d_lat)

def wait_for_confirmation():
    pass

def send_location():
    global current_coords

    # Send current location to server
    pass
