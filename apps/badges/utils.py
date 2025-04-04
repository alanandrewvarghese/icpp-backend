from .models import Badge, UserBadge
import logging

logger = logging.getLogger("badges")

def award_badge_to_user(user, badge_name):
    """
    Utility function to award a badge to a user by Badge Name.

    Args:
        user: The User object to award the badge to.
        badge_name (str): The unique name of the badge to award.

    Returns:
        Badge object if awarded, None if already exists or badge not found
    """
    try:
        # Find the badge by name (now that name is unique)
        badge = Badge.objects.filter(name=badge_name).first()

        if not badge:
            logger.warning(f"Badge with name '{badge_name}' not found, cannot award badge.")
            return None

        # Check if user already has this badge
        if UserBadge.objects.filter(user=user, badge=badge).exists():
            logger.info(f"User '{user.username}' already has the badge '{badge_name}'.")
            return None

        # Award the badge
        user_badge = UserBadge.objects.create(user=user, badge=badge)
        logger.info(f"Badge '{badge_name}' awarded to user '{user.username}'.")
        return badge

    except Exception as e:
        logger.exception(f"Error awarding badge '{badge_name}' to user '{user.username}': {e}")
        return None
