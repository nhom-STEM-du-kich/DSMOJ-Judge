from django.urls import re_path
from . import consumers # Đảm bảo ông đã viết consumers.py rồi nhé!

websocket_urlpatterns = [
    # Cái Regex này phải khớp 100% với cái 'ws/submission/' + subId ở JS nhé Bruv!
    re_path(r'ws/submission/(?P<submission_id>\w+)/$', consumers.SubmissionConsumer.as_asgi()),
]