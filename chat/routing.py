from django.urls import path
from chat.consumers import ChatRoomConsumer, DirectChatConsumer

websocket_urlpatterns = [
    path('ws/chat/<str:room_link>/', ChatRoomConsumer.as_asgi()),
    path('ws/chat/d/<str:username>/', DirectChatConsumer.as_asgi())
]
