
# subscription/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from .models import SubscriptionPlan, UserSubscription
from .serializers import SubscriptionPlanSerializer, UserSubscriptionSerializer
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from users.serializers import UserSerializer  # Use your existing UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

stripe.api_key = settings.STRIPE_SECRET_KEY

class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def create_checkout_session(self, request, pk=None):
        plan = self.get_object()
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': plan.name},
                        'unit_amount': int(plan.price * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url='http://localhost:8000/payment-success/',
                cancel_url='http://localhost:8000/payment-cancel/',
                metadata={
                    'plan_id': plan.id,
                    'user_id': request.user.id,
                }
            )

            return Response({'checkout_url': session.url}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserSubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserSubscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



class SubscribedUsersView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        subscribed_user_ids = UserSubscription.objects.filter(
            is_active=True
        ).values_list('user_id', flat=True).distinct()

        users = User.objects.filter(id__in=subscribed_user_ids)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)



@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # Handle successful payment
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        plan_id = session['metadata']['plan_id']
        user_id = session['metadata']['user_id']
        transaction_id = session['id']

        try:
            user = settings.AUTH_USER_MODEL.objects.get(id=user_id)
            plan = SubscriptionPlan.objects.get(id=plan_id)

            UserSubscription.objects.create(
                user=user,
                plan=plan,
                payment_status='completed',
                transaction_id=transaction_id,
                is_active=True
            )
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'status': 'success'})
