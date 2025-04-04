from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Count
import logging
from django.db import transaction

from apps.progress.models import LessonProgress, ExerciseSubmission
from .models import Badge, UserBadge
from .utils import award_badge_to_user

logger = logging.getLogger('badges')

@receiver(post_save, sender=LessonProgress)
def check_lesson_badges(sender, instance, created, **kwargs):
    """
    Signal handler for processing badges when lesson progress is recorded.
    Automatically awards appropriate badges based on lesson completion milestones.
    """
    if not created:
        return

    user = instance.user
    logger.debug(f"Processing lesson badges for user {user.username}")

    completed_lessons_count = LessonProgress.objects.filter(user=user).count()
    logger.debug(f"User {user.username} has completed {completed_lessons_count} lessons")

    if completed_lessons_count == 1:
        result = award_badge_to_user(user, "Lesson Starter")
        logger.info(f"'Lesson Starter' badge processing - Result: {bool(result)}")

    elif completed_lessons_count == 5:
        result = award_badge_to_user(user, "Lesson Master")
        logger.info(f"'Lesson Master' badge processing - Result: {bool(result)}")


@receiver(post_save, sender=ExerciseSubmission)
def check_exercise_badges(sender, instance, created, **kwargs):
    """
    Signal handler for processing badges when an exercise submission is created or updated.
    Automatically awards appropriate badges based on exercise completion milestones.
    """
    logger.debug(f"Exercise submission signal received: ID={instance.id}, User={instance.user.username}, Correct={instance.is_correct}, Created={created}")

    if not instance.is_correct:
        logger.debug(f"Skipping badge check: submission is not correct")
        return

    user = instance.user
    logger.debug(f"Processing exercise badges for user {user.username}")

    with transaction.atomic():
        completed_exercises = ExerciseSubmission.objects.filter(
            user=user,
            is_correct=True
        ).values('exercise').distinct()

        completed_exercises_count = completed_exercises.count()
        logger.debug(f"User {user.username} has completed {completed_exercises_count} unique exercises correctly")

        first_exercise_badge = Badge.objects.filter(name="First Exercise").exists()
        enthusiast_badge = Badge.objects.filter(name="Exercise Enthusiast").exists()
        master_badge = Badge.objects.filter(name="Exercise Master").exists()
        logger.debug(f"Badge existence check - First Exercise: {first_exercise_badge}, Enthusiast: {enthusiast_badge}, Master: {master_badge}")

        existing_badges = UserBadge.objects.filter(user=user).values_list('badge__name', flat=True)
        logger.debug(f"User {user.username} already has badges: {list(existing_badges)}")

        if completed_exercises_count == 1:
            result = award_badge_to_user(user, "First Exercise")
            logger.info(f"'First Exercise' badge processing - Result: {bool(result)}")

        elif completed_exercises_count == 5:
            result = award_badge_to_user(user, "Exercise Enthusiast")
            logger.info(f"'Exercise Enthusiast' badge processing - Result: {bool(result)}")

        elif completed_exercises_count == 25:
            result = award_badge_to_user(user, "Exercise Master")
            logger.info(f"'Exercise Master' badge processing - Result: {bool(result)}")


def create_default_badges():
    """
    Utility function to create default badges if they don't exist.
    This function is kept for reference only.
    Use the management command instead: python manage.py create_badges
    """
    pass
