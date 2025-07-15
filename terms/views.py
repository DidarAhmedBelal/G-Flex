from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Terms
from .serializers import TermsSerializer


class AdminTermsListCreateView(ListCreateAPIView):
    queryset = Terms.objects.all()
    serializer_class = TermsSerializer
    permission_classes = [IsAdminUser]


class AdminTermsDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Terms.objects.all()
    serializer_class = TermsSerializer
    permission_classes = [IsAdminUser]


class TermsByTypeListView(ListAPIView):
    serializer_class = TermsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        type_param = self.kwargs.get('type')
        return Terms.objects.filter(type=type_param).order_by('-created_at')[:1]
