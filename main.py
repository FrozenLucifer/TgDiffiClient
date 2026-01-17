import json
import asyncio
import os

from src.telegram_client import TGClient
from src import crypto

with open("config.json", "r") as f:
    config = json.load(f)

client = TGClient(config["api_id"], config["api_hash"])
PREFIX = 'crypto:'


async def async_input(prompt=""):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)


def help_info():
    print('''Доступные команды:
    /help - вывести команды
    /d [max] - список диалогов [c-максимальное количество]
    /s <id> - начать защищенный диалог
    /f - отправить файл
    /c - отменить действие
    ''')


async def menu_handler():
    user_id = None
    key = None
    while True:
        text = await async_input()
        if text == '/help':
            help_info()
        elif text.startswith('/d'):
            await client.get_dialogs()
        elif text.startswith('/s '):
            user_id = int(text.split()[1])
            key = await client.start_dialog(user_id)
            client.register_message_handler(user_id, key)
            print(f"Чат с {user_id} начат.")
        elif text == '/c':
            if user_id:
                await client.client.send_message(user_id, PREFIX + "stop")
                user_id = None
            else:
                print("Нечего отменять.")
        elif text == '/f':
            if not user_id:
                print("Сначала начни диалог (/s <id>)")
                continue

            path = await async_input("Путь к файлу: ")
            if not os.path.isfile(path):
                print("Файл не найден")
                continue

            await client.send_file_encrypted(user_id, path, key)

        else:
            if user_id:
                encrypted_message = crypto.encrypt_message(text, key)
                await client.client.send_message(user_id, PREFIX + encrypted_message)
            else:
                print("Неизвестная команда")


async def main():
    await client.start()
    print("CRYPT запущен. /help для команд")
    await asyncio.create_task(menu_handler())
    await client.client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
