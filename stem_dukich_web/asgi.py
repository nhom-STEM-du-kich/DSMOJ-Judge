"""
ASGI config for stem_dukich_web project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import judge.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stem_dukich_web.settings')

application = ProtocolTypeRouter({
    # Giao thức HTTP truyền thống
    "http": get_asgi_application(),
    
    # Giao thức WebSocket cho DSMOJ
    "websocket": AuthMiddlewareStack(
        URLRouter(
            judge.routing.websocket_urlpatterns
        )
    ),
})