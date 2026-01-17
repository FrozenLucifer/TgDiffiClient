import asyncio
import os
import re

import qrcode
from telethon import TelegramClient, events
from telethon.tl.custom.message import Message

from src import diffi, crypto

PREFIX = 'crypto:'


class TGClient:
    def __init__(self, api_id, api_hash, session_name='tgdiffi'):
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.user_id = None
        self.key = None
        self.handler = None

    async def start(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            qr = await self.client.qr_login()
            print("Telegram → Настройки → Устройства → Добавить устройство\n")
            qr_img = qrcode.make(qr.url)
            qr_img.show(title="Telegram QR Login")
            await qr.wait()

    async def get_dialogs(self, max_dialogs=10):
        k = 0
        async for dialog in self.client.iter_dialogs():
            if dialog.is_user and not dialog.entity.bot and not dialog.entity.is_self:
                k += 1
                dialog_info = f"{dialog.name[:28]:30} [id={dialog.id}]"
                if hasattr(dialog, 'message') and dialog.message.message.startswith(PREFIX):
                    dialog_info += ' (!)'
                print(dialog_info)
            if k == max_dialogs:
                break

    async def start_dialog(self, user_id):
        last_message: Message = (await self.client.get_messages(user_id, 1))[0]
        last_message_text = last_message.message
        match = re.match(rf'{re.escape(PREFIX)}start request init (\d+), (\d+), (\d+)', last_message_text)

        if last_message.peer_id.user_id == user_id and match:
            p = int(match.group(1))
            g = int(match.group(2))
            A = int(match.group(3))
            b = diffi.generate_prime(100)
            B = pow(g, b, p)
            K = pow(A, b, p)
            await self.client.send_message(user_id, PREFIX + f"start request accept {B}")
        else:
            p, g = diffi.generate_dh_parameters()
            a = diffi.generate_prime(100)
            A = pow(g, a, p)
            await self.client.send_message(user_id, PREFIX + f"start request init {p}, {g}, {A}")
            while True:
                messages = await self.client.get_messages(user_id, 1)
                if messages:
                    last_message = messages[0].message
                    match_accept = re.match(rf'{re.escape(PREFIX)}start request accept (\d+)', last_message)
                    if match_accept:
                        B = int(match_accept.group(1))
                        break
                await asyncio.sleep(1)
            K = pow(B, a, p)
        return K

    def register_message_handler(self, user_id, key):
        async def handle_new_message(event):
            msg = event.message

            if msg.message == PREFIX + "stop":
                print("Пользователь остановил диалог")
                self.client.remove_event_handler(self.handler)
                return

            if msg.file:
                if msg.message and msg.message.startswith(PREFIX + "file:"):
                    name = msg.message.removeprefix(PREFIX + "file:")
                    path = await msg.download_media()

                    with open(path, 'rb') as f:
                        encrypted = f.read()

                    data = crypto.decrypt_bytes(encrypted, key)

                    out = f"recv_{name}"
                    with open(out, 'wb') as f:
                        f.write(data)

                    print(f"Получен файл: {out}")
                return

            if msg.message and msg.message.startswith(PREFIX):
                text = msg.message.removeprefix(PREFIX)
                text = crypto.decrypt_message(text, key)
                print(f"Получено сообщение: {text}")

        self.handler = self.client.on(events.NewMessage(from_users=[user_id]))(handle_new_message)

    async def send_file_encrypted(self, user_id, path, key):
        with open(path, 'rb') as f:
            data = f.read()

        encrypted = crypto.encrypt_bytes(data, key)

        tmp_path = path + ".crypt"
        with open(tmp_path, 'wb') as f:
            f.write(encrypted)

        await self.client.send_file(
            user_id,
            tmp_path,
            caption=PREFIX + f"file:{os.path.basename(path)}"
        )

        os.remove(tmp_path)
