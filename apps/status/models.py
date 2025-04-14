from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class CompletionStatus(models.Model):
    """Stores simple completion status for various learning elements"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='completion_statuses')

    # Content type fields
    content_type = models.CharField(max_length=20, choices=[
        ('lesson', 'Lesson'),
        ('quiz', 'Quiz'),
        ('exercise', 'Exercise'),
    ])
    content_id = models.PositiveIntegerField()

    # Simple status tracking
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'content_type', 'content_id']
        indexes = [
            models.Index(fields=['user', 'content_type']),
            models.Index(fields=['content_type', 'content_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.content_type} {self.content_id} - {'Completed' if self.completed else 'Incomplete'}"
