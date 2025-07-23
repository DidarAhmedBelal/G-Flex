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
import datetime
import logging
from django.db.models.functions import TruncMonth, TruncWeek

from .models import Donation, DonationCampaign, TotalDonation
from .serializers import (
    DonationSerializer,
    DonationCampaignSerializer,
    CreateDonationCampaignSerializer,
    CreateDonationSessionSerializer,
    RateDonationSerializer,
    UserDonationSummarySerializer,
    AdminDonationSummarySerializer,
    TotalDonationSerializer,
    RateDonationInputSerializer,
)


User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


# ---------------------------
# Donation Campaign Views
# ---------------------------


class FundCollectionView(APIView):
    """
    API view to get the total amount of funds collected from completed donations.
    Accessible by any user.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        total_amount = Donation.objects.filter(payment_status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0.0

        return Response({
            'fund_collection': round(total_amount, 2)
        })


class DonationCampaignViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for managing Donation Campaigns.
    Admins can create, update, and delete campaigns.
    Any user can list and retrieve campaigns.
    """
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
    """
    A ViewSet for viewing Donations.
    Admins can access all donation details.
    Any user can list and retrieve donations.
    Includes a custom action to rate a donation.
    """
    queryset = Donation.objects.all()
    serializer_class = DonationSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'rate_donation']:
            return [AllowAny()]  # Allowing anyone to rate, assuming the 'rate_donation' action is public.
        return [IsAdminUser()]

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def rate_donation(self, request, pk=None):
        """
        Custom action to rate a specific donation.
        """
        donation = self.get_object()
        serializer = RateDonationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        donation.rating = serializer.validated_data['rating']
        donation.save()
        return Response({"detail": "Thank you for your rating!"}, status=status.HTTP_200_OK)


# ---------------------------
# Stripe Checkout & Webhook
# ---------------------------


class CreateDonationCheckoutSessionView(CreateAPIView):
    """
    API view to create a Stripe Checkout Session for donations.
    Accessible by any user.
    """
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
        except (TypeError, ValueError):
            return Response({'error': 'Invalid amount provided'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user if request.user.is_authenticated else None
        donor_name = data.get('donor_name') or (user.get_full_name() if user else 'Guest')
        donor_email = data.get('donor_email') or (user.email if user else None)

        if not donor_email:
            return Response({'error': 'Email is required for guest donations'}, status=status.HTTP_400_BAD_REQUEST)

        metadata = {
            'user_id': str(user.id) if user else '',
            'donor_name': donor_name,
            'donor_email': donor_email,
            'message': message,
            'campaign_id': str(campaign_id) if campaign_id else '',
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
                success_url='myapp://payment-success',
                cancel_url='myapp://payment-cancel',
            )
            return Response({'checkout_url': session.url}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe checkout session creation failed: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RateDonationView(APIView):
    """
    API view to rate a donation (alternative to the action in DonationViewSet).
    Accessible by any user.
    """
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

        return Response({"detail": "Thank you for your rating!"}, status=status.HTTP_200_OK)


# @method_decorator(csrf_exempt, name='dispatch')
# class StripeWebhookView(APIView):
#     """
#     Stripe Webhook endpoint to handle events from Stripe,
#     especially 'checkout.session.completed' to record donations.
#     Requires CSRF exemption as it receives POST requests from Stripe.
#     """
#     permission_classes = [AllowAny]

#     def post(self, request, *args, **kwargs):
#         payload = request.body
#         sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
#         endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

#         try:
#             event = stripe.Webhook.construct_event(
#                 payload=payload,
#                 sig_header=sig_header,
#                 secret=endpoint_secret
#             )
#         except stripe.error.SignatureVerificationError as e:
#             logger.error(f"Stripe signature verification failed: {e}")
#             return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Error parsing webhook payload: {e}")
#             return Response({"error": "Webhook error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         if event['type'] == 'checkout.session.completed':
#             session = event['data']['object']
#             metadata = session.get('metadata', {})
#             transaction_id = session.get('id')
#             amount_total = session.get('amount_total', 0)
#             currency = session.get('currency', 'USD').upper()

#             try:
#                 if Donation.objects.filter(transaction_id=transaction_id).exists():
#                     logger.info("Donation already exists for transaction ID: %s", transaction_id)
#                     return Response({'status': 'duplicate_ignored'}, status=status.HTTP_200_OK)

#                 user = None
#                 user_id = metadata.get('user_id')
#                 if user_id:
#                     user = User.objects.filter(id=user_id).first()

#                 campaign = DonationCampaign.objects.filter(id=metadata.get('campaign_id')).first()

#                 donation = Donation.objects.create(
#                     user=user,
#                     campaign=campaign,
#                     donor_name=metadata.get('donor_name', 'Guest'),
#                     donor_email=metadata.get('donor_email'),
#                     amount=amount_total / 100.0,  # Convert cents to dollars
#                     currency=currency,
#                     message=metadata.get('message', ''),
#                     transaction_id=transaction_id,
#                     payment_status='completed',
#                     is_request=False  # Assuming these are not requests but actual donations
#                 )

#                 if campaign:
#                     campaign.raised_amount += donation.amount
#                     campaign.supporters += 1
#                     campaign.save()

#                 TotalDonation.update_totals(donation.amount)

#                 logger.info("Donation recorded: id=%s, amount=%s", donation.id, donation.amount)
#                 return Response({'status': 'success'}, status=status.HTTP_200_OK)

#             except Exception as e:
#                 logger.error(f"Webhook processing failed for transaction ID {transaction_id}: {e}", exc_info=True)
#                 return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         logger.info("Unhandled webhook event type: %s", event['type'])
#         return Response({'status': 'event_not_handled'}, status=status.HTTP_200_OK)


# ---------------------------
# Summary Views
# ---------------------------


class UserDonationSummaryView(APIView):
    """
    API view for an authenticated user to see their total donated amount.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        total = Donation.objects.filter(user=user, payment_status='completed').aggregate(
            total_amount=Sum('amount')
        )['total_amount'] or 0.0

        serializer = UserDonationSummarySerializer({'total_donated': total})
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminDonationSummaryView(APIView):
    """
    API view for administrators to see a summary of all donations,
    including total donations and donations per user.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_all = Donation.objects.filter(payment_status='completed').aggregate(
            total_all=Sum('amount')
        )['total_all'] or 0.0

        # Annotate user details and sum their donations
        per_user = Donation.objects.filter(payment_status='completed').values(
            'user__id', 'user__email', 'donor_name' # Include donor_name for guests
        ).annotate(user_total=Sum('amount')).order_by('-user_total')

        data = []
        for row in per_user:
            # Prioritize authenticated user's email, then donor_name, then 'Guest'
            display_name = row['user__email'] if row['user__email'] else (row['donor_name'] if row['donor_name'] != 'Guest' else 'Guest')

            data.append({
                'user_id': row['user__id'],
                'user_identifier': display_name, # Use a more generic term as it could be email or guest name
                'user_total': row['user_total']
            })

        serializer = AdminDonationSummarySerializer({
            'total_all_users': total_all,
            'per_user_donations': data
        })

        return Response(serializer.data, status=status.HTTP_200_OK)


class PublicDonationSummaryView(APIView):
    """
    API view to display the overall total donation amount and count.
    Accessible by any user.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        summary = TotalDonation.objects.first()
        if summary:
            serializer = TotalDonationSerializer(summary)
        else:
            # Return a default empty summary if no TotalDonation object exists
            serializer = TotalDonationSerializer({'total_amount': 0.0, 'total_count': 0})
        return Response(serializer.data, status=status.HTTP_200_OK)


class MonthlyDonationGraphView(APIView):
    """
    API view to get weekly donation totals for the current month,
    formatted for a graph. Accessible by any user.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        now = datetime.datetime.now()
        current_month = now.month
        current_year = now.year

        # Filter donations for the current month and annotate by week
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

        # Map: { week_start_date_iso_week_number: total_amount }
        # Note: isocalendar()[1] gives the ISO week number for the year.
        # This might not perfectly align with "Week 1", "Week 2" within a month
        # if the month starts mid-week. For simplicity, we'll use a sequential "Week N" label.
        donation_data = {
            d['week'].isocalendar()[1]: float(d['total_amount']) for d in donations
        }

        # Determine the number of weeks in the current month to accurately represent.
        # This is a simplification; a more robust solution might consider actual week boundaries.
        num_days_in_month = (datetime.date(current_year, current_month % 12 + 1, 1) - datetime.timedelta(days=1)).day
        num_weeks = (num_days_in_month + datetime.date(current_year, current_month, 1).weekday()) // 7 + 1

        data = []
        first_day_of_month = datetime.date(current_year, current_month, 1)
        for i in range(num_weeks):
            # Calculate the start of the current week relative to the first day of the month
            # This logic assumes weeks start on Monday (ISO standard)
            week_start_date = first_day_of_month + datetime.timedelta(days=(i * 7) - first_day_of_month.weekday())
            
            # Ensure week_start_date is within the current month for mapping
            if week_start_date.month != current_month and i > 0: # Avoid issues if month starts mid-week and first "week" is previous month's end
                 continue

            week_number_iso = week_start_date.isocalendar()[1]
            
            # Find the actual week number within the month for labeling
            # This is a bit tricky with ISO weeks spanning month boundaries.
            # For simplicity, we'll label them sequentially 'Week 1', 'Week 2', etc.
            data.append({
                "week": f"Week {i + 1}",
                "total_amount": donation_data.get(week_number_iso, 0.0)
            })

        return Response(data, status=status.HTTP_200_OK)


class YearlyDonationGraphView(APIView):
    """
    API view to get monthly donation totals for the current year,
    formatted for a graph. Accessible by any user.
    """
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

        # Map: { month_number: total_amount }
        donation_data = {d['month'].month: float(d['total_amount']) for d in donations}

        # Build 12-month list ensuring all months are present, with 0 if no donations
        months_data = []
        for month_num in range(1, 13):
            month_name = datetime.date(current_year, month_num, 1).strftime('%B')
            months_data.append({
                "month": month_name,
                "total_amount": donation_data.get(month_num, 0.0)
            })

        return Response(months_data, status=status.HTTP_200_OK)