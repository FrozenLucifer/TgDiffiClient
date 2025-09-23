import asyncio
import telethon
from telethon import TelegramClient, events, sync
import diffi
from telethon.tl.custom.dialog import Dialog
from telethon.tl.custom.message import Message
import re
import crypto
import json

with open("config.json", "r") as f:
    config = json.load(f)

api_id = config["api_id"]
api_hash = config["api_hash"]

client = TelegramClient('session_name', api_id, api_hash)
PREFIX = 'crypto:'


async def get_dialogs(max_dialogs=10):
    k = 0
    dialog: Dialog
    async for dialog in client.iter_dialogs():
        if dialog.is_user and not dialog.entity.bot and not dialog.entity.is_self:
            k += 1
            dialog_info = f"{dialog.name[:28]:30} [id={dialog.id}]"
            if type(dialog.message) == telethon.tl.patched.Message:
                if dialog.message.message.startswith(PREFIX):
                    dialog_info += ' (!)'
                if dialog.message.message.startswith(PREFIX + "start request init"):
                    dialog_info += " start req"
            print(dialog_info)
        if k == max_dialogs:
            break


async def select_user():
    await get_dialogs()
    user_id = int(input("Введите id пользователя: "))
    return user_id


def help_info():
    print('''Доступные команды:
    /help - вывести доступные команды
    /d [max] - список диалогов [c-максимальное количество]
    /s <id> - начать защищенный диалог
    /c - отменить действие
    ''')


async def menu_handler():
    user_id = None
    key = None
    handler = None
    while True:
        text = await async_input()
        if text == '/help':
            help_info()
        elif match := re.match(r'^/d\s*(\d+)?$', text):
            count = match.group(1)
            if count is None:
                await get_dialogs()
            else:
                count = int(count)
                await get_dialogs(count)
        elif match := re.match(r'^/s (\d+)$', text):
            user_id = int(match.group(1))
            key = await start_dialog(user_id)
            print(f'''Начат чат с пользователем {user_id}
Теперь все сообщения кроме команд будут отправлены ему
Завершить диалог - /c''')

            async def handle_new_message(event):
                nonlocal user_id, key
                message: str = event.message.message
                if message == PREFIX + "stop":
                    print("Пользователь остановил диалог")
                    user_id = None
                    client.remove_event_handler(handler)
                else:
                    if message.startswith(PREFIX):
                        message = message.removeprefix(PREFIX)
                        message = crypto.decrypt_message(message, key)

                    print(f"Получено сообщение: {message}")

            handler = client.on(events.NewMessage(from_users=[user_id]))(handle_new_message)

        elif text == '/c':
            if user_id:
                await client.send_message(user_id, PREFIX + "stop")
                print("Диалог остановлен")
                user_id = None
                client.remove_event_handler(handler)
                handler = None
            else:
                print("Нечего отменять.")
        else:
            if user_id:
                encrypted_message = crypto.encrypt_message(text, key)
                await client.send_message(user_id, PREFIX + encrypted_message)
            else:
                print("Неизвестная команда")


async def start_dialog(user_id):
    last_message: Message = (await client.get_messages(user_id, 1))[0]
    last_message_text = last_message.message
    match = re.match(rf'{re.escape(PREFIX)}start request init (\d+), (\d+), (\d+)', last_message_text)

    if last_message.peer_id.user_id == user_id and match:
        p = int(match.group(1))
        g = int(match.group(2))
        A = int(match.group(3))
        b = diffi.generate_prime(100)
        B = pow(g, b, p)
        K = pow(A, b, p)
        await client.send_message(user_id, PREFIX + f"start request accept {B}")
    else:
        p, g = diffi.generate_dh_parameters()
        a = diffi.generate_prime(100)
        A = pow(g, a, p)
        await client.send_message(user_id, PREFIX + f"start request init {p}, {g}, {A}")
        print("Выслано приглашение на начало диалога")
        while True:
            messages = await client.get_messages(user_id, 1)
            if messages:
                last_message = messages[0].message
                match_accept = re.match(rf'{re.escape(PREFIX)}start request accept (\d+)', last_message)
                if match_accept:
                    B = int(match_accept.group(1))
                    break
            await asyncio.sleep(1)

        K = pow(B, a, p)

    return K


@client.on(events.NewMessage(pattern=rf'{re.escape(PREFIX)}start request init (\d+), (\d+), (\d+)'))
async def handle_start_request(event):
    sender = event.sender_id
    print(f"Получено приглашение на начало диалога от пользователя {sender}.")


async def main():
    await client.start()
    await client.connect()
    print("CRYPT запущен. Для команд введите /help")
    await asyncio.create_task(menu_handler())
    await client.run_until_disconnected()


async def async_input(prompt=""):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)


if __name__ == '__main__':
    asyncio.run(main())
