from django.db import models
from django.conf import settings
from apps.lessons.models import Lesson

User = settings.AUTH_USER_MODEL

class Quiz(models.Model):
    """Stores quiz information associated with a lesson."""
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name="quiz")
    title = models.CharField(max_length=255)
    description = models.TextField()
    passing_score = models.IntegerField(default=70)  # Percentage required to pass
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_quizzes", null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.lesson.title}"


class Question(models.Model):
    """Stores quiz questions."""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.quiz.title} - Question {self.order}"


class Choice(models.Model):
    """Stores choices for quiz questions."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} ({'Correct' if self.is_correct else 'Incorrect'})"


class QuizAttempt(models.Model):
    """Tracks user attempts on quizzes."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_attempts")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    score = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score}%"
