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
        fields = ['id', 'title', 'mode', 'created_at']
        read_only_fields = ['created_at', 'mode']

class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_blank=False)
    title = serializers.CharField(required=False)

    def validate(self, data):
        content = data.get("content") or data.get("title")
        if not content:
            raise serializers.ValidationError("Either 'content' or 'title' is required.")
        data["content"] = content.strip()
        return data

class ModeSelectSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(
        choices=[("friend", "Friend"), ("coach", "Coach")],
        label="Mode"
    )
