from django.urls import path
from .views import (
    PublicChatRoomListAPIView, ChatRoomDetailAPIView,
    MessageListCreateAPIView, MessageDetailAPIView,
    CreateChatRoomView, MyDirectChatRoomView, AddRoomMembershipView
)

urlpatterns = [
    path('new-room/', CreateChatRoomView.as_view(), name='create-room'),
    path('direct-rooms/', MyDirectChatRoomView.as_view(), name='create-room'),
    path('add-membership/', AddRoomMembershipView.as_view()),
    path('rooms/', PublicChatRoomListAPIView.as_view(), name='chatroom-list'),
    path('room-detail/<str:room_link>/', ChatRoomDetailAPIView.as_view(), name='chatroom-detail'),

    path('messages/', MessageListCreateAPIView.as_view(), name='message-list'),
    path('messages/<int:pk>/', MessageDetailAPIView.as_view(), name='message-detail'),
]
