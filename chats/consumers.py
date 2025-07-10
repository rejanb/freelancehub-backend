import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': data['message'],
                'sender': data['sender'],
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
        }))
        #
        # import json
        # from channels.generic.websocket import AsyncWebsocketConsumer
        #
        # class ChatConsumer(AsyncWebsocketConsumer):
        #     async def connect(self):
        #         self.room_name = self.scope['url_route']['kwargs']['room_name']
        #         if not self.scope['user'].is_authenticated:
        #             await self.close()
        #             return
        #         self.room_group_name = f'chat_{self.room_name}'
        #         await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        #         await self.accept()
        #
        #     async def disconnect(self, close_code):
        #         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        #
        #     async def receive(self, text_data):
        #         data = json.loads(text_data)
        #         await self.channel_layer.group_send(
        #             self.room_group_name,
        #             {
        #                 'type': 'chat_message',
        #                 'message': data['message'],
        #                 'sender': self.scope['user'].username if self.scope['user'].is_authenticated else 'Anonymous',
        #                 'room': self.room_name,
        #             }
        #         )
        #
        #     async def chat_message(self, event):
        #         await self.send(text_data=json.dumps({
        #             'message': event['message'],
        #             'sender': event['sender'],
        #             'room': event['room'],
        #         }))