from django.contrib import admin
from .models import *

admin.site.register(ChatRoom)
admin.site.register(RoomMembership)
admin.site.register(Message)