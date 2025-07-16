import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from chat.models import Conversation, Message  
from django.contrib.auth.models import AnonymousUser


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.user = self.scope["user"]  # Get logged-in user (if any)

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_msg = data.get('message', '').strip()

        if not user_msg:
            return  # Don't respond to empty messages

        dummy_reply = "Hi! I'm a dummy AI. You said: " + user_msg

        # 🗃️ Save to DB if user is authenticated
        if self.user and not isinstance(self.user, AnonymousUser):
            # Get last conversation or create a new one
            conv = Conversation.objects.filter(user=self.user).last()
            if not conv:
                conv = Conversation.objects.create(user=self.user, title="WebSocket Chat")

            Message.objects.create(conversation=conv, role='user', content=user_msg)
            Message.objects.create(conversation=conv, role='ai', content=dummy_reply)

        # 💬 Send AI reply character-by-character with typing effect
        for ch in dummy_reply:
            await self.send(text_data=json.dumps({"ai_char": ch}))
            await asyncio.sleep(0.05)
