import argparse
import math
import socketio
import asyncio

CONTROL_SERVER_URL = 'http://localhost:8080'
MOVEMENT_SPEED = 0.0001

class HandshakeFailedError(Exception):
    pass

class Drone:
  def __init__(self, drone_id, current_lat, current_lon):
    self.drone_id = drone_id
    self.current_coords = (current_lat, current_lon)
    self.target_coords = None
    self.sio = socketio.AsyncClient()
    self.setup_socket_events()

  async def connect_to_server(self):
    await self.sio.connect(CONTROL_SERVER_URL)
    print('Connected to server')
    await self.handshake()
    await self.send_location()

  async def handshake(self):
    print('Handshaking...')
    response = await self.sio.call('drone_handshake', {'drone_id': self.drone_id})

    if not response['success']:
        print('Handshake failed')
        await self.sio.disconnect()
        raise HandshakeFailedError()
    print('Handshake successful')

  def setup_socket_events(self):
    @self.sio.on('set_target')
    async def set_target(to_coords):
        print('Received target:', to_coords)
        self.target_coords = to_coords.get('coords')

  async def send_location(self):
    await self.sio.emit('drone_location', {'drone_id': self.drone_id, 'current_coords': self.current_coords})

  async def send_arrived(self):
    await self.sio.emit('arrived', {'drone_id': self.drone_id})

  async def fly_to_coords(self):
    if self.target_coords is None:
        return

    await self.send_location()

    target_lat, target_lon = self.target_coords
    current_lat, current_lon = self.current_coords

    # Calculate direction vector
    delta_lat = target_lat - current_lat
    delta_lon = target_lon - current_lon
    distance = math.sqrt(delta_lat ** 2 + delta_lon ** 2)

    # Ensure movement at constant speed
    if distance > MOVEMENT_SPEED:
        scale = MOVEMENT_SPEED / distance
        delta_lat *= scale
        delta_lon *= scale

    # Update current coordinates
    self.current_coords = (current_lat + delta_lat, current_lon + delta_lon)

    # Check if arrived
    if distance < MOVEMENT_SPEED:
      self.current_coords = self.target_coords
      self.target_coords = None
      print('Arrived at', self.current_coords)
      await self.send_arrived()

  async def run_continuous_flight_task(self):
    while True:
      await self.fly_to_coords()
      await asyncio.sleep(0.1)

async def main():
  parser = argparse.ArgumentParser(description='Drone Instance')
  parser.add_argument('--id', help='Drone ID', type=str, required=True)
  parser.add_argument('--current_lat', help='Current Drone Latitude', type=float, default=55.686603495138264)
  parser.add_argument('--current_lon', help='Current Drone Longitude', type=float, default=13.202437928734543)
  args = parser.parse_args()

  drone = Drone(args.id, args.current_lat, args.current_lon)
  await drone.connect_to_server()
  await drone.run_continuous_flight_task()

if __name__ == '__main__':
  try:
    asyncio.run(main())
  except HandshakeFailedError:
    print('Handshake failed. Exiting...')
