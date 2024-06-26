import json
import logging
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, RoomMembership

User = get_user_model()


class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_link = self.scope['url_route']['kwargs']['room_link']
        self.room_group_name = f'chat_{self.room_link}'

        headers = dict(self.scope['headers'])
        token = None
        if b'authorization' in headers:
            auth_header = headers[b'authorization'].decode('utf8')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            await self.close(code=4003, reason="No token provided.")
            return

        try:
            validated_token = UntypedToken(token)
            self.scope['user'] = await self.get_user(validated_token)
        except (InvalidToken, TokenError) as e:
            await self.close(code=4003, reason="Invalid token.")
            return

        if not await self.is_member(self.scope['user'], self.room_link):
            await self.close(code=4003, reason="User is not a member of this room.")
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data.get('message')
        message_type = data.get('message_type', 'TEXT')

        if message_content:
            message = await self.save_message(self.scope['user'], self.room_link, message_content, message_type)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'user': self.scope['user'].username,
                    'message': message_content,
                    'message_type': message_type,
                    'timestamp': message.timestamp.isoformat(),
                }
            )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_user(self, validated_token):
        jwt_auth = JWTAuthentication()
        return jwt_auth.get_user(validated_token)

    @database_sync_to_async
    def is_member(self, user, room_link):
        try:
            room = ChatRoom.objects.get(link=room_link)
            return RoomMembership.objects.filter(user=user, room=room).exists()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, user, room_link, content, message_type):
        room = ChatRoom.objects.get(link=room_link)
        message = Message.objects.create(
            user=user,
            room=room,
            content=content,
            message_type=message_type
        )
        return message



logger = logging.getLogger(__name__)

class DirectChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.other_user_username = self.scope['url_route']['kwargs']['username']
        headers = dict(self.scope['headers'])
        token = self.extract_token(headers)

        if not token:
            await self.close(code=4003, reason="No token provided.")
            return

        try:
            validated_token = UntypedToken(token)
            self.scope['user'] = await self.get_user(validated_token)
        except (InvalidToken, TokenError):
            await self.close(code=4003, reason="Invalid token.")
            return

        if not self.scope['user'].is_authenticated:
            await self.close(code=4003, reason="User not authenticated.")
            return

        try:
            self.other_user = await self.get_other_user(self.other_user_username)
        except User.DoesNotExist:
            await self.close(code=4003, reason="Other user does not exist.")
            return

        if self.scope['user'] == self.other_user:
            await self.close(code=4003, reason="Cannot connect to yourself.")
            return

        self.room_link = self.create_room_link(self.scope['user'].username, self.other_user_username)

        await self.ensure_room_exists(self.room_link)

        await self.channel_layer.group_add(
            self.room_link,
            self.channel_name
        )

        await self.accept()
        logger.info(f"User {self.scope['user'].username} connected to {self.room_link}")

        await self.send_previous_messages()

    async def disconnect(self, close_code):
        logger.info(f"User {self.scope['user'].username} disconnected from {self.room_link} with code {close_code}")
        await self.channel_layer.group_discard(
            self.room_link,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_content = data.get('message')

            if message_content:
                message = await self.save_message(
                    user=self.scope['user'],
                    other_user=self.other_user,
                    content=message_content
                )
                logger.info(f"Message saved: {message.content} from {message.user.username} in room {message.room.link}")

                await self.channel_layer.group_send(
                    self.room_link,
                    {
                        'type': 'chat_message',
                        'user': self.scope['user'].username,
                        'message': message_content,
                        'timestamp': message.timestamp.isoformat(),
                    }
                )
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self.close(code=4003, reason="Error processing message.")

    async def chat_message(self, event):
        try:
            await self.send(text_data=json.dumps(event))
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    def extract_token(self, headers):
        if b'authorization' in headers:
            auth_header = headers[b'authorization'].decode('utf8')
            if auth_header.startswith('Bearer '):
                return auth_header.split(' ')[1]
        return None

    @database_sync_to_async
    def get_user(self, validated_token):
        jwt_auth = JWTAuthentication()
        return jwt_auth.get_user(validated_token)

    @database_sync_to_async
    def get_other_user(self, username):
        return User.objects.get(username=username)

    def create_room_link(self, username1, username2):
        return f'link_{"_".join(sorted([username1, username2]))}'

    @database_sync_to_async
    def ensure_room_exists(self, room_link):
        room, created = ChatRoom.objects.get_or_create(
            link=room_link,
            defaults={
                'name': room_link,
                'room_type': 'DIRECT'
            }
        )
        RoomMembership.objects.get_or_create(user=self.scope['user'], room=room)
        RoomMembership.objects.get_or_create(user=self.other_user, room=room)
        if created:
            logger.info(f"Created new chat room with link: {room_link}")
        return room

    @database_sync_to_async
    def save_message(self, user, other_user, content):
        room_link = self.create_room_link(user.username, other_user.username)
        room = ChatRoom.objects.get(link=room_link)
        return Message.objects.create(
            user=user,
            room=room,
            content=content,
            message_type='TEXT'
        )

    @database_sync_to_async
    def fetch_previous_messages(self, user, other_user):
        room_link = self.create_room_link(user.username, other_user.username)
        try:
            room = ChatRoom.objects.get(link=room_link)
            return Message.objects.filter(room=room).order_by('timestamp')
        except ChatRoom.DoesNotExist:
            return []
    @sync_to_async
    def send_previous_messages(self):
        try:
            messages = self.fetch_previous_messages(self.scope['user'], self.other_user)
            message_list = []
            for message in messages:
                message_list.append({
                    'user': message.user.username,
                    'message': message.content,
                    'timestamp': message.timestamp.isoformat(),
                    'message_type': message.message_type,
                })

            if message_list:
                self.send(text_data=json.dumps({
                    'type': 'previous_messages',
                    'messages': message_list
                }))
                logger.info(f"Sent previous messages to {self.scope['user'].username}")
        except Exception as e:
            logger.error(f"Error sending previous messages: {e}")
            self.close(code=4003, reason="Error sending previous messages")