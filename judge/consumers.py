import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import *
from channels.db import database_sync_to_async
from django.db import transaction
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
class JudgeConsumer(AsyncWebsocketConsumer):
    @database_sync_to_async
    def get_judge(self, api_key):
        # Truy vấn DB một cách húng hẻng
        try:
            return models.JudgeNode.objects.get(api_key=api_key, is_active=True)
        except models.JudgeNode.DoesNotExist:
            return None

    async def connect(self):
        headers = dict(self.scope['headers'])
        auth_key = headers.get(b'x-dsmoj-auth', b'').decode('utf-8')

        # Gọi hàm check DB qua "cầu nối" async
        self.judge = await self.get_judge(auth_key)

        if self.judge:
            await self.accept()
            print(f"Judge {self.judge.name} đã thông nòng Metadata!")
        else:
            await self.close()
            print("Kẻ giả mạo định húp Metadata của nhomstemdukich!")
    async def receive(self, text_data=None, bytes_data=None):
        payload = json.loads(text_data)
    def find_and_lock_task(self):
        """Logic 'gắp' bài từ hàng đợi PD sang JG"""
        with transaction.atomic():
            task = (
                Submission.objects
                .select_for_update(skip_locked=True)
                .filter(status="PD")
                .order_by("created_at")
                .first()
            )
            if not task:
                return None

            # Đánh dấu đang chấm (JG) và gán cho con Judge đang kết nối
            task.status = "JG"
            task.judge_node = self.judge_object # Đã lấy từ connect()
            task.save()
            
            try:
                problem = Problem.objects.get(problem_code=task.problem_code)
                return {
                    "type": "new_task",
                    "id": task.id,
                    "code": task.code,
                    "lang": task.language,
                    "testcases": problem.test_cases,
                    "time_limit": problem.time_limit,
                    "test_view": problem.show_test,
                }
            except Problem.DoesNotExist:
                task.status = "ER"
                task.save()
                return None
    async def receive(self, text_data):
        # Nếu con Judge rảnh, nó bắn tin {"action": "request_task"}
        data = json.loads(text_data)
        if data.get('action') == 'request_task':
            task_data = await self.find_and_lock_task()
            if task_data:
                await self.send(text_data=json.dumps(task_data))
            else:
                await self.send(text_data=json.dumps({"status": "empty"}))