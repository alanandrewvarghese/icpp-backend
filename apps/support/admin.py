from django.contrib import admin
from .models import SupportTicket, TicketResponse

# Register your models here.

admin.site.register(SupportTicket)
admin.site.register(TicketResponse)
