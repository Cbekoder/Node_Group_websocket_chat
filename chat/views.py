from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ChatRoom, RoomMembership, Message
from .serializers import ChatRoomSerializer, RoomMembershipSerializer, MessageSerializer


class CreateChatRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChatRoomSerializer(data=request.data)
        if serializer.is_valid():
            room = serializer.save()

            RoomMembership.objects.create(
                user=request.user,
                room=room,
                role='ADMIN'
            )

            response_data = {
                "message": "Room created successfully",
                "room": {
                    "id": room.id,
                    "name": room.name,
                    "link": room.link,
                    "description": room.description,
                    "room_type": room.room_type,
                    "created_at": room.created_at.isoformat(),
                    "updated_at": room.updated_at.isoformat(),
                },
                "admin": request.user.username
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyDirectChatRoomView(generics.ListAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(
            room_type='DIRECT',
            memberships__user=user
        ).distinct()

# View for listing and creating chat rooms
class PublicChatRoomListAPIView(generics.ListAPIView):
    queryset = ChatRoom.objects.filter(room_type="PUBLIC")
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]

# View for retrieving, updating, and deleting a specific chat room
class ChatRoomDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_link):
        chatroom = get_object_or_404(ChatRoom, link=room_link)
        if chatroom.room_type == "PUBLIC":
            return Response(ChatRoomSerializer(chatroom).data, status=status.HTTP_200_OK)
        elif chatroom.room_type == "PRIVATE":
            if RoomMembership.objects.filter(room=chatroom, user=request.user).exists():
                return Response(ChatRoomSerializer(chatroom).data, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'You do not have permission to view this room.'},
                                status=status.HTTP_403_FORBIDDEN)



class AddRoomMembershipView(APIView):
    """
    API view to handle adding a user to a chat room.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        room_link = request.query_params.get('room_link')
        if not room_link:
            return Response({'error': 'room_link query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        room = get_object_or_404(ChatRoom, link=room_link)
        if RoomMembership.objects.filter(user=user, room=room).exists():
            return Response({'detail': 'User is already a member of this room.'}, status=status.HTTP_400_BAD_REQUEST)
        membership = RoomMembership(user=user, room=room, role='MEMBER')  # Default to MEMBER role
        membership.save()
        serializer = RoomMembershipSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# View for listing and creating messages
class MessageListCreateAPIView(generics.ListCreateAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# View for retrieving, updating, and deleting a specific message
class MessageDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

