from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'avatar_url', 'onboarding_complete', 'email_verified', 'created_at']
        read_only_fields = ['id', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['email', 'password', 'name', 'role']

    def validate_role(self, value):
        if value not in ['founder', 'investor']:
            raise serializers.ValidationError("Role must be either 'founder' or 'investor'")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        user.email_verified = False
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid email or password")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")
            if not user.email_verified:
                raise serializers.ValidationError("Please verify your email before logging in")
            data['user'] = user
        else:
            raise serializers.ValidationError("Must include email and password")

        return data