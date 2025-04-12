from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import QuizAttempt
from apps.badges.utils import award_badge_to_user
import logging

logger = logging.getLogger("quiz")

@receiver(post_save, sender=QuizAttempt)
def check_quiz_badges(sender, instance, created, **kwargs):
    """
    Signal handler for processing badges when quizzes are passed.
    """
    if not created or not instance.passed:
        return

    user = instance.user
    logger.debug(f"Processing quiz badges for user {user.username}")

    # Count passed quizzes
    passed_quizzes_count = QuizAttempt.objects.filter(
        user=user,
        passed=True
    ).values('quiz').distinct().count()

    logger.debug(f"User {user.username} has passed {passed_quizzes_count} unique quizzes")

    if passed_quizzes_count == 1:
        result = award_badge_to_user(user, "Quiz Novice")
        logger.info(f"'Quiz Novice' badge processing - Result: {bool(result)}")

    elif passed_quizzes_count == 5:
        result = award_badge_to_user(user, "Quiz Master")
        logger.info(f"'Quiz Master' badge processing - Result: {bool(result)}")
