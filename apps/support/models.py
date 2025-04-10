from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class SupportTicket(models.Model):
    class TicketStatus(models.TextChoices):
        OPEN = 'open', _('Open')
        RESOLVED = 'resolved', _('Resolved')

    class TicketType(models.TextChoices):
        LESSON = 'lesson', _('Lesson')
        EXERCISE = 'exercise', _('Exercise')
        OTHER = 'other', _('Other')

    title = models.CharField(max_length=255)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.OPEN
    )
    ticket_type = models.CharField(
        max_length=20,
        choices=TicketType.choices,
        default=TicketType.OTHER
    )
    related_lesson = models.CharField(max_length=255, blank=True, null=True)
    related_exercise = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.status}"


class TicketResponse(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_admin_response = models.BooleanField(default=False)

    def __str__(self):
        return f"Response to {self.ticket.title} by {self.user.username}"
