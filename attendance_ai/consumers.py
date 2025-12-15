from channels.generic.websocket import AsyncJsonWebsocketConsumer

class AdminConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")

        if not user or not user.is_authenticated or not user.is_staff:
            await self.close()
            return

        await self.channel_layer.group_add("admins", self.channel_name)
        await self.accept()
        print("✅ Admin connected")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("admins", self.channel_name)
        print("⚠️ Admin disconnected")

    async def admin_event(self, event):
        await self.send_json(event["data"])
