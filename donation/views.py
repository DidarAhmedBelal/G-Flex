from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Sum
from django.conf import settings
from django.contrib.auth import get_user_model
import stripe
from django.db.models.functions import TruncMonth, TruncYear
from collections import defaultdict
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import datetime
from .models import Donation, DonationCampaign, TotalDonation
from .serializers import (
    DonationSerializer,
    DonationCampaignSerializer,
    CreateDonationCampaignSerializer,
    CreateDonationSessionSerializer,
    RateDonationSerializer,
    UserDonationSummarySerializer,
    AdminDonationSummarySerializer,
    PerUserDonationSerializer,
    TotalDonationSerializer
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Sum
from .models import Donation
from django.db.models.functions import TruncMonth, TruncYear
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Sum
from donation.models import Donation
import datetime
from collections import OrderedDict

from django.db.models.functions import TruncMonth, TruncWeek


User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY


# ---------------------------
# Donation Campaign Views
# ---------------------------



class FundCollectionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        total_amount = Donation.objects.filter(payment_status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0.0

        return Response({
            'fund_collection': round(total_amount, 2)
        })



class DonationCampaignViewSet(viewsets.ModelViewSet):
    queryset = DonationCampaign.objects.all().order_by('-created_at')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CreateDonationCampaignSerializer
        return DonationCampaignSerializer


# ---------------------------
# Donation Views
# ---------------------------

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
        serializer.is_valid(raise_exception=True)
        donation.rating = serializer.validated_data['rating']
        donation.save()
        return Response({"detail": "Thank you for your rating!"})


# ---------------------------
# Stripe Checkout & Webhook
# ---------------------------

class CreateDonationCheckoutSessionView(CreateAPIView):
    serializer_class = CreateDonationSessionSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        amount = data.get('amount')
        campaign_id = data.get('campaign_id')
        message = data.get('message', '')

        try:
            stripe_amount = int(amount * 100)
        except:
            return Response({'error': 'Invalid amount'}, status=400)

        user = request.user if request.user.is_authenticated else None
        donor_name = data.get('donor_name') or (user.get_full_name() if user else 'Guest')
        donor_email = data.get('donor_email') or (user.email if user else None)

        if not donor_email:
            return Response({'error': 'Email is required for guest'}, status=400)

        metadata = {
            'user_id': str(user.id) if user else '',
            'donor_name': donor_name,
            'donor_email': donor_email,
            'message': message,
            'campaign_id': str(campaign_id),
        }

        try:
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
                success_url = 'myapp://payment-success',
                cancel_url = 'myapp://payment-cancel',
            )
            return Response({'checkout_url': session.url})
        except Exception as e:
            return Response({'error': str(e)}, status=500)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from .models import Donation
from .serializers import RateDonationInputSerializer

class RateDonationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RateDonationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        donation_id = serializer.validated_data['donation_id']
        rating = serializer.validated_data['rating']

        try:
            donation = Donation.objects.get(id=donation_id)
        except Donation.DoesNotExist:
            return Response({"detail": "Donation not found."}, status=status.HTTP_404_NOT_FOUND)

        donation.rating = rating
        donation.save()

        return Response({"detail": "Thank you for your rating!"})


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except Exception:
            return Response({'error': 'Invalid signature'}, status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            metadata = session.get('metadata', {})
            amount = session.get('amount_total', 0) / 100.0
            currency = session.get('currency', 'USD').upper()
            transaction_id = session.get('id')

            try:
                user = None
                if metadata.get('user_id'):
                    user = User.objects.filter(id=metadata['user_id']).first()

                campaign = DonationCampaign.objects.filter(id=metadata.get('campaign_id')).first()

                donation = Donation.objects.create(
                    user=user,
                    campaign=campaign,
                    donor_name=metadata.get('donor_name', 'Guest'),
                    donor_email=metadata.get('donor_email'),
                    amount=amount,
                    currency=currency,
                    message=metadata.get('message', ''),
                    transaction_id=transaction_id,
                    payment_status='completed',
                    is_request=False
                )

                if campaign:
                    campaign.raised_amount += amount
                    campaign.supporters += 1
                    campaign.save()

                TotalDonation.update_totals(amount)
            except Exception as e:
                return Response({'error': str(e)}, status=500)

        return Response({'status': 'success'})


# ---------------------------
# Summary Views
# ---------------------------

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

        data = [
            {
                'user_id': row['user__id'],
                'user_email': row['user__email'] or 'Guest',
                'user_total': row['user_total']
            }
            for row in per_user if row['user__id']
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




class MonthlyDonationGraphView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        now = datetime.datetime.now()
        current_month = now.month
        current_year = now.year

        # Filter donations for current month
        donations = (
            Donation.objects.filter(
                payment_status='completed',
                donated_at__year=current_year,
                donated_at__month=current_month
            )
            .annotate(week=TruncWeek('donated_at'))
            .values('week')
            .annotate(total_amount=Sum('amount'))
            .order_by('week')
        )

        # Map: { week_start_date: total_amount }
        donation_data = {
            d['week'].isocalendar()[1]: float(d['total_amount']) for d in donations
        }

        # Build list of 4 weeks (assumption: max 4 weeks in month)
        data = []
        first_day = datetime.date(current_year, current_month, 1)
        for i in range(4):
            week_start = first_day + datetime.timedelta(days=i * 7)
            week_number = week_start.isocalendar()[1]
            data.append({
                "week": f"Week {i + 1}",
                "total_amount": donation_data.get(week_number, 0.0)
            })

        return Response(data)


class YearlyDonationGraphView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        current_year = datetime.datetime.now().year

        # Get monthly donation totals for current year
        donations = (
            Donation.objects.filter(
                payment_status='completed',
                donated_at__year=current_year
            )
            .annotate(month=TruncMonth('donated_at'))
            .values('month')
            .annotate(total_amount=Sum('amount'))
            .order_by('month')
        )

        donation_data = {d['month'].month: float(d['total_amount']) for d in donations}

        # Build 12-month list
        months = []
        for month in range(1, 13):
            month_name = datetime.date(1900, month, 1).strftime('%B')
            months.append({
                "month": month_name,
                "total_amount": donation_data.get(month, 0.0)
            })

        return Response(months)
