import random
import string
from django.db import models
from django.conf import settings

class ChatRoom(models.Model):
    """Model representing a chat room."""
    ROOM_TYPES = (
        ('PUBLIC', 'Public'),
        ('PRIVATE', 'Private'),
        ('DIRECT', 'Direct'),
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    room_type = models.CharField(max_length=7, choices=ROOM_TYPES, default='PUBLIC')
    link = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.room_type == 'PRIVATE' and not self.link:
            self.link = self.generate_random_link()
            while ChatRoom.objects.filter(link=self.link).exists():
                self.link = self.generate_random_link()
        elif self.room_type == 'PUBLIC' and self.link:
            if not self.is_valid_link_format(self.link):
                raise ValueError("The provided link format is invalid.")
            if ChatRoom.objects.filter(link=self.link).exists():
                raise ValueError("The provided link is already in use.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Room: {self.name} ({self.get_room_type_display()})'

    def generate_random_link(self):
        """Generate a random link for private rooms."""
        letters_and_digits = string.ascii_letters + string.digits
        return ''.join(random.choices(letters_and_digits, k=13))

    def is_valid_link_format(self, link):
        """Check if the link contains only letters, numbers, and underscores."""
        allowed_chars = string.ascii_letters + string.digits + '_'
        return all(char in allowed_chars for char in link)



class RoomMembership(models.Model):
    """Tracks membership and roles of users in chat rooms."""
    ROLES = (
        ('ADMIN', 'Admin'),
        ('MEMBER', 'Member'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=6, choices=ROLES, default='MEMBER')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'room')

    def __str__(self):
        return f'{self.user.username} in {self.room.name} as {self.get_role_display()}'

class Message(models.Model):
    """Model representing a message in a chat room."""
    MESSAGE_TYPES = (
        ('TEXT', 'Text'),
        ('IMAGE', 'Image'),
        ('FILE', 'File'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField(blank=True, null=True)
    message_type = models.CharField(max_length=5, choices=MESSAGE_TYPES, default='TEXT')
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['timestamp']  # Order messages by timestamp by default

    def __str__(self):
        return f'Message by {self.user.username} in {self.room.name} at {self.timestamp}'

