from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Donation
from .serializers import DonationSerializer
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import stripe
import json
from donation.models import Donation
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


stripe.api_key = settings.STRIPE_SECRET_KEY

class DonationViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.CreateModelMixin,
                      viewsets.GenericViewSet):
    queryset = Donation.objects.all()
    serializer_class = DonationSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAdminUser()]  

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user, payment_status='completed')
        else:
            serializer.save(payment_status='completed')

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def rate_donation(self, request, pk=None):
        donation = self.get_object()
        rating = request.data.get('rating')

        if rating and rating.isdigit() and 1 <= int(rating) <= 5:
            donation.rating = int(rating)
            donation.save()
            return Response({"detail": "Thank you for your rating!"})
        return Response({"error": "Invalid rating (must be 1-5)."}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_donation_checkout_session(request):
    try:
        amount = request.data.get('amount')
        donor_name = request.data.get('name') or "Guest"
        donor_email = request.data.get('email')
        message = request.data.get('message', '')

        if not amount:
            return JsonResponse({'error': 'Amount is required'}, status=400)

        # Stripe amount must be in cents
        stripe_amount = int(float(amount) * 100)

        metadata = {
            'donor_name': donor_name,
            'donor_email': donor_email or '',
            'message': message,
            'user_id': str(request.user.id) if request.user.is_authenticated else '',
        }

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': 'Donation'},
                    'unit_amount': stripe_amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            metadata=metadata,
            success_url='http://localhost:8000/donation-success/',
            cancel_url='http://localhost:8000/donation-cancel/',
        )

        return JsonResponse({'checkout_url': session.url})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)






@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # Handle checkout session for donation
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        metadata = session.get('metadata', {})
        transaction_id = session['id']
        amount = session['amount_total'] / 100.0  # from cents

        try:
            user = None
            user_id = metadata.get('user_id')
            if user_id:
                user = User.objects.get(id=user_id)

            Donation.objects.create(
                user=user,
                donor_name=metadata.get('donor_name'),
                donor_email=metadata.get('donor_email'),
                amount=amount,
                currency='USD',
                message=metadata.get('message', ''),
                payment_status='completed',
                transaction_id=transaction_id
            )
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'status': 'success'})
