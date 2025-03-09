from django.db import models
from django.conf import settings
User = settings.AUTH_USER_MODEL # To easily use our custom user model

class LessonProgress(models.Model):
    """Tracks a user's progress in a lesson."""
    user = models.ForeignKey(User, on_delete=models.CASCADE) # Link to the User model
    lesson = models.ForeignKey("lessons.Lesson", on_delete=models.CASCADE) # Link to the Lesson model in the lessons app
    completed_at = models.DateTimeField(auto_now_add=True) # Automatically saves the time when a lesson is completed

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} completed"

class ExerciseSubmission(models.Model):
    """Stores student submissions for exercises."""
    user = models.ForeignKey(User, on_delete=models.CASCADE) # Link to the User model
    exercise = models.ForeignKey("lessons.Exercise", on_delete=models.CASCADE) # Link to the Exercise model in the lessons app
    submitted_code = models.TextField() # Stores the code submitted by the user
    execution_result = models.ForeignKey("sandbox.ExecutionResult", on_delete=models.SET_NULL, null=True, blank=True) # Links to the result of code execution from sandbox app
    submitted_at = models.DateTimeField(auto_now_add=True) # Automatically saves the time of submission
    is_correct = models.BooleanField(default=False)  # To mark if the submission is correct (we can decide how to check this later)

    def __str__(self):
        return f"{self.user.username} - {self.exercise.title} Submission"