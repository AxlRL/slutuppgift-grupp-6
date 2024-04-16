import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clong", help='current longitude of drone location', type=float)
    parser.add_argument("--clat", help='current latitude of drone location', type=float)
    parser.add_argument("--id", help ='drones ID', type=str, required=True)
    args = parser.parse_args()

    drone_id = args.id

    while True:
        new_order = get_order()
