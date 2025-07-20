# models.py
from django.db import models
from django.conf import settings

class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=255, blank=True, null=True)
    mode = models.CharField(max_length=10, choices=(('friend', 'Friend'), ('coach', 'Coach')), blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=(('user', 'User'), ('ai', 'AI')))
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    