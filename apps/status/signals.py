from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.progress.models import LessonProgress, ExerciseSubmission
from apps.quiz.models import QuizAttempt
from .models import CompletionStatus
import logging

logger = logging.getLogger('status')

@receiver(post_save, sender=LessonProgress)
def update_lesson_status(sender, instance, created, **kwargs):
    """Update lesson completion status when LessonProgress is created/updated"""
    CompletionStatus.objects.update_or_create(
        user=instance.user,
        content_type='lesson',
        content_id=instance.lesson.id,
        defaults={'completed': True}
    )
    logger.debug(f"Updated lesson status for user {instance.user.username}, lesson {instance.lesson.id}")

@receiver(post_save, sender=QuizAttempt)
def update_quiz_status(sender, instance, created, **kwargs):
    """Update quiz completion status when a quiz is passed"""
    if instance.passed:
        CompletionStatus.objects.update_or_create(
            user=instance.user,
            content_type='quiz',
            content_id=instance.quiz.id,
            defaults={'completed': True}
        )
        logger.debug(f"Updated quiz status for user {instance.user.username}, quiz {instance.quiz.id}")

@receiver(post_save, sender=ExerciseSubmission)
def update_exercise_status(sender, instance, created, **kwargs):
    """Update exercise completion status when an exercise is submitted correctly"""
    if instance.is_correct:
        CompletionStatus.objects.update_or_create(
            user=instance.user,
            content_type='exercise',
            content_id=instance.exercise.id,
            defaults={'completed': True}
        )
        logger.debug(f"Updated exercise status for user {instance.user.username}, exercise {instance.exercise.id}")
