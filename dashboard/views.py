# dashboard/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema

from .models import SiteMetric, Earning
from .serializers import DashboardStatsSerializer, MonthlyUserCountSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class DashboardStatsView(APIView):

    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        responses={200: DashboardStatsSerializer}
    )
    def get(self, request, *args, **kwargs):
        now = timezone.now()
        start_of_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_last_month = (start_of_current_month - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_users_count = User.objects.filter(date_joined__gte=start_of_current_month).count()

        active_users_count = User.objects.filter(last_login__gte=now - timedelta(days=30)).count()

        total_views = SiteMetric.objects.aggregate(Sum('views_count'))['views_count__sum'] or 0
        total_visits = SiteMetric.objects.aggregate(Sum('visits_count'))['visits_count__sum'] or 0

        current_month_earning_obj = Earning.objects.filter(month=start_of_current_month).first()
        monthly_earnings = current_month_earning_obj.amount if current_month_earning_obj else 0.00

        data = {
            'new_users': new_users_count,
            'active_users': active_users_count,
            'total_views': total_views,
            'total_visits': total_visits,
            'monthly_earnings': monthly_earnings,
        }
        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MonthlyUserTrendView(APIView):

    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        responses={200: MonthlyUserCountSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        now = timezone.now()
        current_year = now.year
        last_year = current_year - 1

 
        current_year_users = User.objects.filter(
            date_joined__year=current_year
        ).annotate(
            month=TruncMonth('date_joined')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')

  
        last_year_users = User.objects.filter(
            date_joined__year=last_year
        ).annotate(
            month=TruncMonth('date_joined')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')

        monthly_data = {f"{month:02d}": {"this_year_users": 0, "last_year_users": 0} for month in range(1, 13)}

        for data in current_year_users:
            month_str = data['month'].strftime('%m')
            monthly_data[month_str]['this_year_users'] = data['count']

        for data in last_year_users:
            month_str = data['month'].strftime('%m')
            monthly_data[month_str]['last_year_users'] = data['count']


        response_data = []
        for month_num in range(1, 13):
            month_key = f"{month_num:02d}"
            response_data.append({
                "month": timezone.datetime(current_year, month_num, 1).strftime('%b'), # e.g., Jan, Feb
                "this_year_users": monthly_data[month_key]['this_year_users'],
                "last_year_users": monthly_data[month_key]['last_year_users'],
            })

        serializer = MonthlyUserCountSerializer(response_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)