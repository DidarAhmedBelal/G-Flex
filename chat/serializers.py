from rest_framework import serializers
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'role', 'content', 'created_at']
        read_only_fields = ['role', 'created_at']

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at']
        read_only_fields = ['created_at']

class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_blank=False)
    title = serializers.CharField(required=False)

    def validate(self, data):
        content = data.get("content") or data.get("title")
        if not content:
            raise serializers.ValidationError("Either 'content' or 'title' is required.")
        data["content"] = content.strip()
        return data
