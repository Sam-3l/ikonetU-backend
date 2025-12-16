from rest_framework import serializers
from .models import Video
from apps.accounts.serializers import UserSerializer
from apps.profiles.serializers import FounderProfileSerializer


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = '__all__'
        read_only_fields = ['id', 'founder', 'view_count', 'created_at', 'updated_at']


class VideoWithFounderSerializer(serializers.ModelSerializer):
    founder = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = '__all__'

    def get_founder(self, obj):
        from apps.profiles.models import FounderProfile
        
        user_data = {
            'id': obj.founder.id,
            'name': obj.founder.name,
            'avatarUrl': obj.founder.avatar_url
        }
        
        try:
            profile = FounderProfile.objects.get(user=obj.founder)
            profile_data = FounderProfileSerializer(profile).data
        except FounderProfile.DoesNotExist:
            profile_data = None
        
        return {
            'user': user_data,
            'profile': profile_data
        }

class VideoHistorySerializer(serializers.ModelSerializer):
    """Serializer for video history - includes URL"""
    class Meta:
        model = Video
        fields = ['id', 'title', 'url', 'thumbnail_url', 'duration', 'status', 'is_current', 'view_count', 'created_at']