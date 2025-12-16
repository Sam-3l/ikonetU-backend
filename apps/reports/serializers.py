from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ['id', 'reporter', 'created_at', 'resolved_by', 'resolved_at']


class ReportDetailSerializer(serializers.ModelSerializer):
    reporter = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()
    reported_user = serializers.SerializerMethodField()
    resolved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = '__all__'

    def get_reporter(self, obj):
        return {
            'id': obj.reporter.id,
            'name': obj.reporter.name,
            'email': obj.reporter.email,
        }

    def get_video(self, obj):
        if obj.video:
            return {
                'id': obj.video.id,
                'title': obj.video.title,
                'url': obj.video.url,
                'thumbnail_url': obj.video.thumbnail_url,
            }
        return None

    def get_reported_user(self, obj):
        if obj.reported_user:
            return {
                'id': obj.reported_user.id,
                'name': obj.reported_user.name,
                'email': obj.reported_user.email,
            }
        return None

    def get_resolved_by_name(self, obj):
        if obj.resolved_by:
            return obj.resolved_by.name
        return None