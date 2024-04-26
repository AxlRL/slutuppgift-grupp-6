import argparse
import math
import socketio
import asyncio

drone_id = None
current_coords = None
target_coords = None

sio = socketio.AsyncClient()

@sio.on("fly_to_coordinates")
async def fly_to_coordinates(to_coords):
    global target_coords
    target_coords = to_coords

async def run_continuous_task():
    while True:
        await fly_to_coords()
        await asyncio.sleep(1)

async def main():
    global drone_id, current_coords

    ## Parse Arguments
    parser = argparse.ArgumentParser(description="Drone Control System")
    parser.add_argument("--id", help='Drone ID', type=str, required=True)
    parser.add_argument("--current_lat", help='Current Drone Latitude', type=float, default=55.7076368)
    parser.add_argument("--current_lon", help='Current Drone Longitude', type=float, default=13.1880542)
    args = parser.parse_args()

    drone_id = args.id
    current_coords = (args.current_lat, args.current_lon)

    ## Connect To Command Server
    await sio.connect("http://localhost:8080")

    await send_location()
    await run_continuous_task()

async def fly_to_coords():
    global current_coords, target_coords

    if target_coords is None:
        return

    await send_location()

    target_lat, target_lon = target_coords

    current_lat, current_lon = current_coords

    print("Flying to", target_coords, "from", current_coords)

    current_coords = (
        current_lat + (target_lat - current_lat) * 0.1,
        current_lon + (target_lon - current_lon) * 0.1,
    )

    distance = math.sqrt((target_lon - current_lon) ** 2 + (target_lat - current_lat) ** 2)

    if distance < 0.0001:
        current_coords = target_coords
        await send_arrived()

@sio.on("connect")
async def send_hello():
    global sio, drone_id

    await sio.emit("hello", { "drone_id": drone_id })

async def send_location():
    global sio, drone_id, current_coords

    await sio.emit("drone_location", { "drone_id": drone_id, "current_coords": current_coords })

async def send_arrived():
    global sio, drone_id

    await sio.emit("arrived", { "drone_id": drone_id })

if __name__ == "__main__":
    asyncio.run(main())
