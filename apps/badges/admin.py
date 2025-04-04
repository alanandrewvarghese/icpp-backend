from django.contrib import admin
from .models import Badge, UserBadge

# Register your models here.

admin.site.register(Badge)
admin.site.register(UserBadge)
