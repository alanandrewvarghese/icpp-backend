from django.db import models
from django.conf import settings
User = settings.AUTH_USER_MODEL

class Badge(models.Model):
    """Represents a badge that users can earn"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=100)  # CSS class or filename for badge icon
    requirements = models.TextField(blank=True)  # Description of how to earn the badge
    created_at = models.DateTimeField(auto_now_add=True)

    # Badge categories
    CATEGORY_CHOICES = [
        ('achievement', 'Achievement'),
        ('progress', 'Progress'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='achievement')

    def __str__(self):
        return self.name

class UserBadge(models.Model):
    """Records badges earned by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')  # Each user can earn a specific badge only once

    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"
