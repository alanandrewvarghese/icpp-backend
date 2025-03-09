from django.contrib import admin
from .models import LessonProgress, ExerciseSubmission

# Register your models here.
admin.site.register(LessonProgress)
admin.site.register(ExerciseSubmission)