from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Conversation, Message
from .serializers import ConversationSerializer, SendMessageSerializer  


class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
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

      
        if not conv.title:
            conv.title = f"User: {user_msg[:50]}"
            conv.save()

        Message.objects.create(conversation=conv, role='user', content=user_msg)

        dummy_reply = "Hi! I'm a dummy AI. You said: " + user_msg

        # openai.api_key = settings.OPENAI_API_KEY

        # # prepare chat history
        # history = [
        #     {"role": msg.role, "content": msg.content}
        #     for msg in conv.messages.order_by("created_at")
        # ]
        # history.append({"role": "user", "content": user_msg})

        # try:
        #     response = openai.ChatCompletion.create(
        #         model="gpt-3.5-turbo",
        #         messages=history,
        #     )
        #     ai_reply = response.choices[0].message["content"]
        # except Exception as e:
        #     return Response({"error": f"OpenAI Error: {str(e)}"}, status=500)


        Message.objects.create(conversation=conv, role='ai', content=dummy_reply)

        return Response({
            "User": user_msg,
            "AI": dummy_reply
        }, status=200)
