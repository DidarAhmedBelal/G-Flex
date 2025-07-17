from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render

from .models import Conversation, Message
from .serializers import ConversationSerializer, SendMessageSerializer, MessageSerializer
from .chat import generate_response, extract_text_from_pdf, chunk_text, create_embeddings_batch, precompute_label_embeddings

import os
import pickle

# === Base directory of your project (where manage.py is) ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# === Full path to your PDF file ===
pdf_path = os.path.join(BASE_DIR, "chat", "The_Apple_and_The_Stone (10) (1) (2).pdf")

# Extract text from PDF
text = extract_text_from_pdf(pdf_path)

# Chunk the extracted text
chunks = chunk_text(text)

# Path for embeddings cache file
embedding_path = os.path.join(BASE_DIR, "chat", "pdf_embeddings.pkl")

# Load or create embeddings
if os.path.exists(embedding_path):
    with open(embedding_path, "rb") as f:
        embeddings = pickle.load(f)
else:
    embeddings = create_embeddings_batch(chunks)
    with open(embedding_path, "wb") as f:
        pickle.dump(embeddings, f)

# Precompute label embeddings for motivational quotes
label_embeddings = precompute_label_embeddings()


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

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def send_message(self, request, pk=None):
        conv = self.get_object()
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_msg = serializer.validated_data['content'].strip()

        mode = request.data.get("mode", "friend").lower()

        if not conv.title:
            conv.title = f"User: {user_msg[:50]}"
            conv.save()

        Message.objects.create(conversation=conv, role='user', content=user_msg)

        # Get previous user messages in this conversation
        previous = list(conv.messages.filter(role='user').values_list('content', flat=True))

        # Generate AI response
        ai_reply = generate_response(user_msg, chunks, embeddings, label_embeddings, previous, mode)

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
