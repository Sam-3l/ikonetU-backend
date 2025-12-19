from rest_framework import serializers
from .models import Video
from apps.accounts.models import User
from apps.profiles.models import FounderProfile


class FounderUserSerializer(serializers.ModelSerializer):
    """Serializer for user info in video feed"""
    class Meta:
        model = User
        fields = ['id', 'name', 'avatar_url']


class FounderProfileSerializer(serializers.ModelSerializer):
    """Serializer for founder profile info"""
    class Meta:
        model = FounderProfile
        fields = ['company_name', 'sector', 'stage', 'location', 'bio']


class FounderWithProfileSerializer(serializers.Serializer):
    """Combined founder user + profile data"""
    user = FounderUserSerializer(source='*')
    profile = serializers.SerializerMethodField()
    
    def get_profile(self, obj):
        try:
            profile = FounderProfile.objects.get(founder=obj)
            return FounderProfileSerializer(profile).data
        except FounderProfile.DoesNotExist:
            return None


class VideoSerializer(serializers.ModelSerializer):
    """Basic video serializer"""
    class Meta:
        model = Video
        fields = [
            'id', 'founder_id', 'url', 'thumbnail_url', 
            'title', 'duration', 'status', 'view_count',
            'is_current', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'view_count', 'created_at', 'updated_at']


class VideoWithFounderSerializer(serializers.ModelSerializer):
    """Video serializer with full founder details for feed"""
    founder = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = [
            'id', 'founder_id', 'url', 'thumbnail_url',
            'title', 'duration', 'status', 'view_count',
            'is_current', 'created_at', 'founder'
        ]
    
    def get_founder(self, obj):
        """Get founder with their profile data"""
        try:
            user = obj.founder
            profile = None
            try:
                profile = FounderProfile.objects.get(founder=user)
            except FounderProfile.DoesNotExist:
                pass
            
            return {
                'user': {
                    'id': str(user.id),
                    'name': user.name,
                    'avatar_url': user.avatar_url
                },
                'profile': {
                    'company_name': profile.company_name if profile else 'Unknown Company',
                    'sector': profile.sector if profile else 'Tech',
                    'stage': profile.stage if profile else 'Seed',
                    'location': profile.location if profile else 'Unknown',
                    'bio': profile.bio if profile else ''
                } if profile else None
            }
        except Exception as e:
            print(f"Error serializing founder: {e}")
            return None


class VideoHistorySerializer(serializers.ModelSerializer):
    """Video serializer for history view"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Video
        fields = [
            'id', 'url', 'thumbnail_url', 'title', 
            'duration', 'status', 'status_display',
            'view_count', 'is_current', 'created_at'
        ]