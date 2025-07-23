from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render

from .models import Conversation, Message
from .serializers import (
    ConversationSerializer,
    SendMessageSerializer,
    MessageSerializer,
    ModeSelectSerializer
)
from .chat import (
    generate_response,
    extract_text_from_pdf,
    chunk_text,
    create_embeddings_batch
)


import os
import pickle

# === Base directory of your project (where manage.py is) ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# === Full path to your PDF file ===
pdf_path = os.path.join(BASE_DIR, "chat", "The_Apple_and_The_Stone (10) (1) (2).pdf")

# Extract and chunk text
text = extract_text_from_pdf(pdf_path)
chunks = chunk_text(text)

# === Load or generate PDF embeddings ===
embedding_path = os.path.join(BASE_DIR, "chat", "pdf_embeddings.pkl")
if os.path.exists(embedding_path):
    with open(embedding_path, "rb") as f:
        embeddings = pickle.load(f)
else:
    embeddings = create_embeddings_batch(chunks)
    with open(embedding_path, "wb") as f:
        pickle.dump(embeddings, f)


class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Conversation.objects.none()
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        serializer_class=ModeSelectSerializer  
    )
    def select_mode(self, request):
        serializer = self.get_serializer(data=request.data)  
        serializer.is_valid(raise_exception=True)
        mode = serializer.validated_data["mode"]

        conv = Conversation.objects.create(user=request.user, mode=mode)

        return Response({
            "message": f"Mode '{mode}' selected.",
            "conversation_id": conv.id
        }, status=201)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def send_message(self, request, pk=None):
        conv = self.get_object()

        if not conv.mode:
            return Response({"error": "Mode not set. Please set mode first."}, status=400)

        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_msg = serializer.validated_data['content'].strip()

        if not conv.title:
            conv.title = f"User: {user_msg[:50]}"
            conv.save()

        Message.objects.create(conversation=conv, role='user', content=user_msg)


        # Gather previous messages (user and AI) for conversation history
        previous_msgs = list(conv.messages.order_by('created_at').values_list('role', 'content'))
        prev_queries = [f"{role.capitalize()}: {content}" for role, content in previous_msgs]
        ai_reply = generate_response(user_msg, chunks, embeddings, prev_queries, conv.mode)

        Message.objects.create(conversation=conv, role='ai', content=ai_reply)

        return Response({
            "User": user_msg,
            "AI": ai_reply
        }, status=200)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def messages(self, request, pk=None):
        conv = self.get_object()
        messages = conv.messages.order_by("created_at")
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)


def websocket_test_view(request):
    return render(request, "chat/test_socket.html")
