import asyncio
import websockets
import json
import os

async def connect():
    uri = "ws://localhost:4002"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("Підключено до WebSocket сервера")
                async for message in websocket:
                    data = json.loads(message)
                    # Добавьте логику обработки данных здесь
                    #os.system('cls')
                    print(data)

        except websockets.exceptions.ConnectionClosed as e:
            print(f"З'єднання закрито: {e.reason}")
            print("Спроба перепідключення...")
            await asyncio.sleep(5)  # Подождать перед переподключением

        except Exception as e:
            print(f"Помилка WebSocket: {e}")
            print("Спроба перепідключення...")
            await asyncio.sleep(5)  # Подождать перед переподключением


# Асинхронная функция запуска соединения
async def main():
    await connect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Програма завершена користувачем")
