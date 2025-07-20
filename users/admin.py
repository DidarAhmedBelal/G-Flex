from django.contrib import admin

# Register your models here.
from users.models import User, FriendBirthday, WishMessage
admin.site.register(User)
admin.site.register(FriendBirthday)
admin.site.register(WishMessage)