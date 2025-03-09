from django.urls import path
from .api_views import RecordLessonCompletionAPIView, ExerciseSubmissionAPIView # Import our API views

urlpatterns = [
    path('lessons/<int:lesson_id>/complete/', RecordLessonCompletionAPIView.as_view(), name='record-lesson-completion'), # URL for lesson completion
    path('exercises/<int:exercise_id>/submit/', ExerciseSubmissionAPIView.as_view(), name='submit-exercise'), # URL for exercise submission
]