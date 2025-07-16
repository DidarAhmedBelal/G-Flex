from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Conversation, Message
from .serializers import ConversationSerializer, SendMessageSerializer, MessageSerializer
from django.shortcuts import render

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Avoid errors during Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Conversation.objects.none()

        user = self.request.user
        if user.is_authenticated:
            return self.queryset.filter(user=user)
        return self.queryset.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def send_message(self, request, pk=None):
        conv = self.get_object()

        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_msg = serializer.validated_data['content'].strip()

        # If no title, set it from the first message
        if not conv.title:
            conv.title = f"User: {user_msg[:50]}"
            conv.save()

        # Save user message
        Message.objects.create(conversation=conv, role='user', content=user_msg)

        # Generate dummy AI reply (replace with OpenAI call if needed)
        dummy_reply = "Hi! I'm a dummy AI. You said: Hi! I'm a dummy AI. You said: Hi! I'm a dummy AI. You said: Hi! I'm a dummy AI. You said: Hi! I'm a dummy AI. You said: Hi! I'm a dummy AI. You said: " + user_msg
        Message.objects.create(conversation=conv, role='ai', content=dummy_reply)

        return Response({
            "User": user_msg,
            "AI": dummy_reply
        }, status=200)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def messages(self, request, pk=None):
        conv = self.get_object()
        messages = conv.messages.order_by("created_at")
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)


def websocket_test_view(request):
    return render(request, "chat/test_socket.html")