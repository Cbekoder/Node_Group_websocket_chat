from rest_framework import serializers
from .models import ChatRoom, RoomMembership, Message
from user.serializers import AccountSerializer

class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ('id', 'name', 'link', 'description', 'room_type', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

class RoomMembershipSerializer(serializers.ModelSerializer):
    user = AccountSerializer(read_only=True)
    room = serializers.PrimaryKeyRelatedField(queryset=ChatRoom.objects.all())
    class Meta:
        model = RoomMembership
        fields = ['id', 'user', 'room', 'role', 'joined_at']
        read_only_fields = ['id', 'user', 'role', 'joined_at']

class MessageSerializer(serializers.ModelSerializer):
    user = AccountSerializer(read_only=True)
    room = serializers.PrimaryKeyRelatedField(queryset=ChatRoom.objects.all())
    parent = serializers.PrimaryKeyRelatedField(queryset=Message.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Message
        fields = ('id', 'user', 'room', 'content', 'message_type', 'file', 'parent', 'timestamp', 'updated_at')
        read_only_fields = ('timestamp', 'updated_at')

    def validate(self, attrs):
        # Ensure content or file is provided based on message type
        if attrs.get('message_type') == 'TEXT' and not attrs.get('content'):
            raise serializers.ValidationError("Text message must contain content.")
        if attrs.get('message_type') in ['IMAGE', 'FILE'] and not attrs.get('file'):
            raise serializers.ValidationError("Image/File message must contain a file.")
        return attrs

