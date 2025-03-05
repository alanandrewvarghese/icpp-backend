from django.db import models
from django.conf import settings
User = settings.AUTH_USER_MODEL

class Lesson(models.Model):
    """Stores information about each lesson."""
    title = models.CharField(max_length=255)
    description = models.TextField()
    content = models.TextField()  # Supports markdown or rich text
    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_lessons", null=True, blank=True) # Creator of the lesson

    def __str__(self):
        return self.title

class Exercise(models.Model):
    """Stores coding exercises associated with lessons."""
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="exercises")
    title = models.CharField(max_length=255)
    description = models.TextField()
    starter_code = models.TextField(blank=True, null=True)
    solution_code = models.TextField(blank=True, null=True)
    test_cases = models.JSONField(default=list)  # Stores test cases as JSON
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_exercises", null=True, blank=True) # Creator of the exercise

    def __str__(self):
        return self.title