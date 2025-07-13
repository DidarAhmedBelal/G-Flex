# donation/views.py
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAdminUser, AllowAny
from .models import Donation
from .serializers import DonationSerializer
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema

class DonationViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.CreateModelMixin,
                      viewsets.GenericViewSet):

    queryset = Donation.objects.all()
    serializer_class = DonationSerializer

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny] 
        else:
            permission_classes = [IsAdminUser] 
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user, payment_status='completed') 
        else:
            serializer.save(payment_status='completed') 