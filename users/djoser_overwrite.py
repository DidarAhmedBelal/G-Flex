#djoser_overwrite.py
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.timezone import now
from djoser import utils
from django.conf import settings

class CustomUserViewSet(UserViewSet):

    @action(["post"], detail=False)
    def reset_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.get_user()

        if user:
            context = {"user": user}
            to = [utils.get_user_email(user)]
            settings.EMAIL.password_reset(self.request, context).send(to)

        return Response({"message": "Password reset email sent successfully"}, status=status.HTTP_200_OK)

    @action(["post"], detail=False)
    def reset_password_confirm(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.user.set_password(serializer.data["new_password"])
        if hasattr(serializer.user, "last_login"):
            serializer.user.last_login = now()
        serializer.user.save()

        if getattr(settings, "PASSWORD_CHANGED_EMAIL_CONFIRMATION", False):
            context = {"user": serializer.user}
            to = [utils.get_user_email(serializer.user)]
            settings.EMAIL.password_changed_confirmation(self.request, context).send(to)

        return Response({"message": "Password has been reset successfully"}, status=status.HTTP_200_OK)
