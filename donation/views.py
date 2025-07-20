# from rest_framework import viewsets, mixins, status
# from rest_framework.permissions import IsAdminUser, AllowAny
# from rest_framework.response import Response
# from rest_framework.decorators import action, api_view, permission_classes
# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse
# from django.conf import settings
# from django.contrib.auth import get_user_model
# import stripe
# from rest_framework.generics import CreateAPIView
# from django.utils.decorators import method_decorator
# from rest_framework.views import APIView
# from .models import Donation
# from .serializers import (
#     DonationSerializer,
#     CreateDonationSessionSerializer,
#     RateDonationSerializer
# )

# from drf_spectacular.utils import extend_schema

# User = get_user_model()
# stripe.api_key = settings.STRIPE_SECRET_KEY


# class DonationViewSet(mixins.ListModelMixin,
#                       mixins.RetrieveModelMixin,
#                       mixins.CreateModelMixin,
#                       viewsets.GenericViewSet):
#     queryset = Donation.objects.all()
#     serializer_class = DonationSerializer

#     def get_permissions(self):
#         if self.action in ['list', 'retrieve', 'rate_donation']:
#             return [AllowAny()]
#         return [IsAdminUser()]

#     @extend_schema(
#         request=RateDonationSerializer,
#         responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}}
#     )
#     @action(detail=True, methods=['post'], permission_classes=[AllowAny])
#     def rate_donation(self, request, pk=None):
#         donation = self.get_object()
#         serializer = RateDonationSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=400)

#         donation.rating = serializer.validated_data['rating']
#         donation.save()
#         return Response({"detail": "Thank you for your rating!"})
    
#     def create(self, request, *args, **kwargs):
#         if not request.user.is_staff:
#             return Response({'error': 'Only admin can create donation requests'}, status=403)

#         data = request.data.copy()
#         data['is_request'] = True

#         serializer = self.get_serializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()

#         return Response(serializer.data, status=201)



# class CreateDonationCheckoutSessionView(CreateAPIView):
#     serializer_class = CreateDonationSessionSerializer
#     permission_classes = [AllowAny]

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         data = serializer.validated_data
#         amount = data.get('amount')
#         donation_id = data.get('donation_id') 
#         message = data.get('message', '')

#         try:
#             stripe_amount = int(float(amount) * 100)
#         except ValueError:
#             return Response({'error': 'Invalid amount'}, status=400)

#         donation_request = None
#         if donation_id:
#             donation_request = Donation.objects.filter(id=donation_id, is_request=True).first()
#             if not donation_request:
#                 return Response({'error': 'Invalid donation_id or not a donation request'}, status=400)

#         user = request.user if request.user.is_authenticated else None

#         if user:
#             full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
#             donor_name = full_name if full_name else user.email
#             donor_email = user.email
#         else:
#             donor_name = data.get('donor_name') or "Guest"
#             donor_email = data.get('donor_email')
#             if not donor_email:
#                 return Response({'error': 'Email is required for guest'}, status=400)

#         metadata = {
#             'donor_name': donor_name,
#             'donor_email': donor_email,
#             'message': message,
#             'user_id': str(user.id) if user else '',
#         }

#         if donation_request:
#             metadata['donation_request_id'] = str(donation_request.id)

#         try:
#             session = stripe.checkout.Session.create(
#                 payment_method_types=['card'],
#                 line_items=[{
#                     'price_data': {
#                         'currency': 'usd',
#                         'product_data': {'name': f'Donation{" for Request #" + str(donation_request.id) if donation_request else ""}'},
#                         'unit_amount': stripe_amount,
#                     },
#                     'quantity': 1,
#                 }],
#                 mode='payment',
#                 metadata=metadata,
#                 success_url='http://localhost:8000/donation-success/',
#                 cancel_url='http://localhost:8000/donation-cancel/',
#             )

#             return Response({'checkout_url': session.url})
#         except Exception as e:
#             return Response({'error': str(e)}, status=500)

# @method_decorator(csrf_exempt, name='dispatch')
# class StripeWebhookView(APIView):
#     permission_classes = [AllowAny]

#     def post(self, request, *args, **kwargs):
#         payload = request.body
#         sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
#         endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

#         try:
#             event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
#         except (ValueError, stripe.error.SignatureVerificationError):
#             return Response({'error': 'Invalid webhook'}, status=400)

#         if event['type'] == 'checkout.session.completed':
#             session = event['data']['object']
#             metadata = session.get('metadata', {})
#             transaction_id = session.get('id')
#             amount = session.get('amount_total') / 100.0

#             try:
#                 user = None
#                 user_id = metadata.get('user_id')
#                 if user_id:
#                     user = User.objects.filter(id=user_id).first()

#                 donor_name = metadata.get('donor_name', 'Guest')
#                 donor_email = metadata.get('donor_email', '')
#                 message = metadata.get('message', '')

#                 donation_request = None
#                 donation_request_id = metadata.get('donation_request_id')
#                 if donation_request_id:
#                     donation_request = Donation.objects.filter(id=donation_request_id, is_request=True).first()

#                 Donation.objects.create(
#                     user=user,
#                     donor_name=donor_name,
#                     donor_email=donor_email,
#                     amount=amount,
#                     currency=session.get('currency', 'USD').upper(),
#                     message=message,
#                     payment_status='completed',
#                     transaction_id=transaction_id,
#                     is_request=False,
#                 )

#             except Exception as e:
#                 return Response({'error': str(e)}, status=500)

#         return Response({'status': 'success'})


from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
import stripe
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from django.db.models import Sum
from .models import Donation
from .serializers import (
    DonationSerializer,
    CreateDonationSessionSerializer,
    RateDonationSerializer
)
from django.db import models
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from django.db.models import Sum
from .models import Donation, TotalDonation
from .serializers import (
    UserDonationSummarySerializer,
    AdminDonationSummarySerializer,
    PerUserDonationSerializer,
    TotalDonationSerializer
)


User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY


class DonationViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    queryset = Donation.objects.all()
    serializer_class = DonationSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'rate_donation']:
            return [AllowAny()]
        return [IsAdminUser()]

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def rate_donation(self, request, pk=None):
        donation = self.get_object()
        serializer = RateDonationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        donation.rating = serializer.validated_data['rating']
        donation.save()
        return Response({"detail": "Thank you for your rating!"})

class CreateDonationCheckoutSessionView(CreateAPIView):
    serializer_class = CreateDonationSessionSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        amount = data.get('amount')
        message = data.get('message', '')

        try:
            stripe_amount = int(float(amount) * 100)
        except ValueError:
            return Response({'error': 'Invalid amount'}, status=400)

        user = request.user if request.user.is_authenticated else None

        if user:
            full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            donor_name = full_name or user.email
            donor_email = user.email
        else:
            donor_name = data.get('donor_name') or "Guest"
            donor_email = data.get('donor_email')
            if not donor_email:
                return Response({'error': 'Email is required for guest'}, status=400)

        metadata = {
            'donor_name': donor_name,
            'donor_email': donor_email,
            'message': message,
            'user_id': str(user.id) if user else '',
        }

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': 'General Donation'},
                        'unit_amount': stripe_amount,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                metadata=metadata,
                success_url='http://localhost:8000/donation-success/',
                cancel_url='http://localhost:8000/donation-cancel/',
            )

            return Response({'checkout_url': session.url})
        except Exception as e:
            return Response({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response({'error': 'Invalid webhook'}, status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            metadata = session.get('metadata', {})
            transaction_id = session.get('id')
            amount = session.get('amount_total') / 100.0

            try:
                user = None
                user_id = metadata.get('user_id')
                if user_id:
                    user = User.objects.filter(id=user_id).first()

                Donation.objects.create(
                    user=user,
                    donor_name=metadata.get('donor_name', 'Guest'),
                    donor_email=metadata.get('donor_email', ''),
                    amount=amount,
                    currency=session.get('currency', 'USD').upper(),
                    message=metadata.get('message', ''),
                    payment_status='completed',
                    transaction_id=transaction_id,
                    is_request=False,
                )
            except Exception as e:
                return Response({'error': str(e)}, status=500)

        return Response({'status': 'success'})



class UserDonationSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        total = Donation.objects.filter(user=user, payment_status='completed').aggregate(
            total_amount=Sum('amount')
        )['total_amount'] or 0.0

        serializer = UserDonationSummarySerializer({'total_donated': total})
        return Response(serializer.data)


class AdminDonationSummaryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_all = Donation.objects.filter(payment_status='completed').aggregate(
            total_all=Sum('amount')
        )['total_all'] or 0.0

        per_user = Donation.objects.filter(payment_status='completed').values(
            'user__id', 'user__email'
        ).annotate(user_total=Sum('amount')).order_by('-user_total')

        # Convert for serializer
        data = [
            {
                'user_id': row['user__id'],
                'user_email': row['user__email'] or 'Guest',
                'user_total': row['user_total']
            }
            for row in per_user if row['user__id'] is not None
        ]

        serializer = AdminDonationSummarySerializer({
            'total_all_users': total_all,
            'per_user_donations': data
        })

        return Response(serializer.data)


class PublicDonationSummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        summary = TotalDonation.objects.first()
        if summary:
            serializer = TotalDonationSerializer(summary)
        else:
            serializer = TotalDonationSerializer({'total_amount': 0.0, 'total_count': 0})
        return Response(serializer.data)
