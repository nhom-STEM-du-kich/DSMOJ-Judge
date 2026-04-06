import json
from channels.generic.websocket import AsyncWebsocketConsumer

class SubmissionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.submission_id = self.scope['url_route']['kwargs']['submission_id']
        self.group_name = f'submission_{self.submission_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def submission_update(self, event):
        status = event['status']
    
        # Bắn nó xuống Client (JS ở Frontend)
        await self.send(text_data=json.dumps({
            'status': status,
            'result_log': event.get('result_log', '')
        }))
    