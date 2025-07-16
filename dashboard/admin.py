from django.contrib import admin

# Register your models here.
from dashboard.models import SiteMetric, Earning
admin.site.register(SiteMetric)
admin.site.register(Earning)