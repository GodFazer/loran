from quart import Quart, render_template, jsonify, websocket, request
from quart_cors import cors
import asyncio
import websockets
import requests
import json
import logging
from config import CONFIG
import time
from calcobject import custom_least_squares, tdoa_error

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Quart(__name__)
app = cors(app, allow_origin="*")

initial_points = [
    {'sourceId': 'source1', 'x': 0, 'y': 0, 'id': 'initial1', 'receivedAt': int(time.time() * 1000)},
    {'sourceId': 'source2', 'x': 0, 'y': 100, 'id': 'initial2', 'receivedAt': int(time.time() * 1000)},
    {'sourceId': 'source3', 'x': 100, 'y': 0, 'id': 'initial3', 'receivedAt': int(time.time() * 1000)}
]

cached_data = initial_points.copy()
clients = set()


def process_data(raw_data):
    for point in cached_data:
        if point['sourceId'] == raw_data.get('sourceId'):
            point['receivedAt'] = raw_data.get('receivedAt')
            point['id'] = raw_data.get('id')
            return point
    return {
        'x': raw_data.get('x', 0),
        'y': raw_data.get('y', 0),
        'sourceId': raw_data.get('sourceId'),
        'id': raw_data.get('id'),
        'receivedAt': raw_data.get('receivedAt', int(time.time() * 1000))
    }


async def connect_to_source():
    while True:
        try:
            async with websockets.connect(CONFIG['SOURCE_WEBSOCKET_URI']) as websocket:
                logger.info("Підключено до WebSocket серверу джерела даних")
                async for message in websocket:
                    await handle_message(message)
        except websockets.exceptions.ConnectionClosed as e:
            logger.error(f"Зєднання з джерелом даних закрито: {e.reason}")
        except Exception as e:
            logger.error(f"Помилка WebSocket при підключенні до джерела: {e}")

        logger.info("Спроба перепідключення до джерела даних через 5 секунд...")
        await asyncio.sleep(5)


async def handle_message(message):
    try:
        x1, y1 = 0, 0
        x2, y2 = 100000, 0
        x3, y3 = 0, 100000
        c = 3e8 / 10e8
        CoordObj = {}

        initial_guess = [50000, 50000]

        raw_data = json.loads(message)
        processed_data = process_data(raw_data)
        if processed_data not in cached_data:
            cached_data.append(processed_data)

        source1_id = None
        for item in cached_data:
            if item['sourceId'] == 'source1':
                source1_id = item['id']
                break

        if source1_id:
            matching_items = [item for item in cached_data if item['id'] == source1_id]

            if len(matching_items) == 3:
                delta_t12 = (matching_items[0]['receivedAt'] - matching_items[1]['receivedAt']) / 1000 * 10e8
                delta_t13 = (matching_items[0]['receivedAt'] - matching_items[2]['receivedAt']) / 1000 * 10e8
                x_opt, y_opt, iterations = custom_least_squares(tdoa_error, initial_guess,args=(x1, y1, x2, y2, x3, y3, delta_t12, delta_t13, c))
                CoordObj['Object'] = "Object"
                CoordObj['x_Obj'] = x_opt/1000
                CoordObj['y_Obj'] = y_opt/1000
                processed_data.update(CoordObj)

        print(processed_data)
        await notify_clients(processed_data)
    except json.JSONDecodeError:
        logger.error(f"Отримано неправильне JSON повідомлення: {message}")
    except Exception as e:
        logger.error(f"Помилка при обробці повідомлення: {e}")


async def notify_clients(data):
    if clients:
        disconnected_clients = set()
        for ws in clients:
            try:
                await ws.send(json.dumps(data))
            except Exception as e:
                logger.error(f"Помилка при відправці даних клієнту: {e}")
                disconnected_clients.add(ws)

        clients.difference_update(disconnected_clients)


@app.before_serving
async def before_serving():
    app.add_background_task(connect_to_source)


@app.route('/')
async def index():
    url = "http://localhost:4002/config"
    response = requests.get(url, headers={})

    if response.status_code == 200:
        json_data = response.json()
    else:
        json_data = {"objectSpeed": 0}  

    return await render_template('index.html', json_data=json_data)


@app.websocket('/ws')
async def ws():
    client = websocket._get_current_object()
    clients.add(client)
    try:
        for data in cached_data:
            await client.send(json.dumps(data))

        while True:
            data = await client.receive()
            logger.info(f"Отримано повідомлення від клієнта: {data}")
            await client.send(json.dumps({"status": "received", "message": "Повідомлення отримано!"}))
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Помилка в WebSocket зєднанні з клієнтом: {e}")
    finally:
        clients.remove(client)


@app.route('/get-data', methods=['GET'])
async def get_data():
    return jsonify(cached_data)

@app.route('/get-config', methods=['POST'])
async def get_config():
    url = "http://localhost:4001/config"

    response = requests.get(url, headers={"Content-Type": "application/json"})

    if response.status_code == 200:
        response_data = response.json()
        satelliteSpeed = response_data.get('satelliteSpeed', 0)
        objectSpeed = response_data.get('objectSpeed', 0)

        return jsonify({
            "objectSpeed": objectSpeed,
        })
    else:
        return jsonify({
            "status_code": response.status_code,
            "error": "Не вийшло отримати дані"
        })


@app.route('/send-config', methods=['POST', 'OPTIONS'])
async def send_config():
    if request.method == 'OPTIONS':
        response = await app.make_default_options_response()
        response.headers['Access-Control-Allow-Methods'] = 'POST'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    data = await request.get_json()

    url = "http://localhost:4002/config"

    try:
        response = requests.post(url,
                                 headers={"Content-Type": "application/json"},
                                 json=data)

        return jsonify({
            "status_code": response.status_code,
            "response": "Конфігурація оновлена" if response.status_code == 200 else "Помилка оновлення конфігурації",
            "updated_config": data
        })
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status_code": 500,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host=CONFIG['HOST'], port=CONFIG['PORT'], debug=CONFIG['DEBUG'])