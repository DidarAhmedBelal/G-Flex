from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator

from .models import SubscriptionPlan, UserSubscription
from .serializers import SubscriptionPlanSerializer, UserSubscriptionSerializer
from users.serializers import UserSerializer
from donation.models import Donation, DonationCampaign, TotalDonation

import stripe
import logging

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionPlanSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]

    def get_queryset(self):
        return SubscriptionPlan.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = get_object_or_404(SubscriptionPlan.objects.all(), pk=kwargs['pk'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @swagger_auto_schema(auto_schema=None)
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def create_checkout_session(self, request, pk=None):
        plan = get_object_or_404(SubscriptionPlan.objects.all(), pk=pk)

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
                success_url='myapp://payment-success',
                cancel_url='myapp://payment-cancel',
                metadata={
                    'plan_id': str(plan.id),
                    'user_id': str(request.user.id),
                    'subscription': 'true'
                }
            )
            return Response({'checkout_url': session.url}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({'detail': f'Stripe error: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': f'Unexpected error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserSubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserSubscription.objects.none()
        return UserSubscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        subscription = self.get_object()
        if subscription.user != request.user:
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)

        if not subscription.is_active:
            return Response({'detail': 'Subscription is already inactive.'}, status=status.HTTP_400_BAD_REQUEST)

        subscription.is_active = False
        subscription.save()

        user = subscription.user
        user.is_subscribed = False
        user.save()

        return Response({'status': 'Subscription cancelled.'})


class SubscribedUsersView(APIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(auto_schema=None)
    def get(self, request):
        subscribed_user_ids = UserSubscription.objects.filter(
            is_active=True
        ).values_list('user_id', flat=True).distinct()

        users = User.objects.filter(id__in=subscribed_user_ids)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class UnifiedStripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=endpoint_secret
            )
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Stripe signature verification failed: {e}")
            return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error parsing webhook payload: {e}")
            return Response({"error": "Webhook error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            metadata = session.get('metadata', {})
            transaction_id = session.get('id')
            logger.info("Stripe session completed received for transaction: %s", transaction_id)

            if metadata.get("donation") == "true":
                try:
                    if Donation.objects.filter(transaction_id=transaction_id).exists():
                        return Response({'status': 'duplicate_ignored'}, status=status.HTTP_200_OK)

                    user = User.objects.filter(id=metadata.get('user_id')).first()
                    campaign = DonationCampaign.objects.filter(id=metadata.get('campaign_id')).first()

                    donation = Donation.objects.create(
                        user=user,
                        campaign=campaign,
                        donor_name=metadata.get('donor_name', 'Guest'),
                        donor_email=metadata.get('donor_email'),
                        amount=session.get('amount_total', 0) / 100.0,
                        currency=session.get('currency', 'USD').upper(),
                        message=metadata.get('message', ''),
                        transaction_id=transaction_id,
                        payment_status='completed',
                        is_request=False
                    )

                    if campaign:
                        campaign.raised_amount += donation.amount
                        campaign.supporters += 1
                        campaign.save()

                    TotalDonation.update_totals(donation.amount)
                    logger.info("Donation recorded: id=%s", donation.id)
                    return Response({'status': 'donation_success'}, status=status.HTTP_200_OK)

                except Exception as e:
                    logger.error(f"Donation webhook failed: {e}", exc_info=True)
                    return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            elif metadata.get("subscription") == "true":
                try:
                    user = User.objects.get(id=metadata.get('user_id'))
                    plan = SubscriptionPlan.objects.get(id=metadata.get('plan_id'))

                    if not UserSubscription.objects.filter(user=user, transaction_id=transaction_id).exists():
                        UserSubscription.objects.filter(user=user, is_active=True).update(is_active=False)

                        UserSubscription.objects.create(
                            user=user,
                            plan=plan,
                            payment_status='completed',
                            transaction_id=transaction_id,
                            is_active=True
                        )

                        user.is_subscribed = True
                        user.save()

                    logger.info("Subscription activated for user: %s", user.id)
                    return Response({'status': 'subscription_success'}, status=status.HTTP_200_OK)

                except Exception as e:
                    logger.error(f"Subscription webhook failed: {e}", exc_info=True)
                    return Response({'error': f'Subscription error: {str(e)}'}, status=500)

        logger.info("Unhandled webhook event type: %s", event['type'])
        return Response({'status': 'event_not_handled'}, status=status.HTTP_200_OK)
