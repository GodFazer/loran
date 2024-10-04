import asyncio
import websockets
import json
import matplotlib.pyplot as plt
import numpy as np

async def receive_data():
    uri = "ws://localhost:4000"
    async with websockets.connect(uri) as websocket:
        while True:
            try:
                data = await websocket.recv()
                data_json = json.loads(data)
                process_data(data_json)
            except websockets.ConnectionClosed:
                print("З'єднання закрито")
                break
            except Exception as e:
                print(f"Error: {e}")

def process_data(data):
    try:
        c = 300000
        distances = [(c * echo['time']) / 2 for echo in data['echoResponses']]
        if distances:  # Check if the list is not empty
            angles = np.full(len(distances), data['scanAngle'])
            max_distance = max(distances)
            plot_data(distances, angles, max_distance)
    except Exception as e:
        print(f"Error: {e}")

def plot_data(distances, angles, max_distance):
    try:
        plt.clf()
        plt.subplot(projection='polar')
        plt.scatter(np.radians(angles), distances, s=100)
        plt.title("Візуалізація цілей радару")
        plt.xlabel("Кут (градуси)")
        plt.ylabel("Відстань (км)")
        plt.ylim(0, max_distance + 100)
        plt.pause(0.1)
    except Exception as e:
        print(f"Error: {e}")

async def main():
    plt.ion()
    plt.figure(figsize=(8, 8))
    while True:
        try:
            await receive_data()
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(1)  # retry after 1 second

if __name__ == "__main__":
    asyncio.run(main())