from rest_framework import serializers
from .models import Account
class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'bio', 'avatar', 'last_seen')
        read_only_fields = ('last_seen',)

# serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'password', 'password_confirm', 'bio', 'avatar']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        # Remove password_confirm as it's not part of the Account model
        validated_data.pop('password_confirm')
        user = User(
            username=validated_data['username'],
            bio=validated_data.get('bio', ''),
            avatar=validated_data.get('avatar', None)
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

