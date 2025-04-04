from django.core.management.base import BaseCommand
from apps.badges.models import Badge

class Command(BaseCommand):
    help = "Creates default badges if they don't already exist."

    def handle(self, *args, **kwargs):
        badge_definitions = [
            {"name": "Lesson Starter", "description": "Awarded for completing your first lesson", "icon": "starter.png"},
            {"name": "Lesson Master", "description": "Awarded for completing 5 lessons", "icon": "lesson_master.png"},
            {"name": "First Exercise", "description": "Awarded for correctly completing your first exercise", "icon": "first_exercise.png"},
            {"name": "Exercise Enthusiast", "description": "Awarded for correctly completing 5 exercises", "icon": "enthusiast.png"},
            {"name": "Exercise Master", "description": "Awarded for correctly completing 25 exercises", "icon": "exercise_master.png"},
        ]

        created_count = 0
        for badge_def in badge_definitions:
            badge, created = Badge.objects.get_or_create(
                name=badge_def["name"],
                defaults={
                    "description": badge_def["description"],
                    "icon": badge_def["icon"],
                    "category": "achievement",
                }
            )
            if created:
                created_count += 1

        if created_count:
            self.stdout.write(self.style.SUCCESS(f"Successfully created {created_count} new badges."))
        else:
            self.stdout.write(self.style.WARNING("No new badges were created. All default badges already exist."))
