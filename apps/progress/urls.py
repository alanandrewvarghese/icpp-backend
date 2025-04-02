from django.urls import path
from .api_views import RecordLessonCompletionAPIView, ExerciseSubmissionAPIView, LessonProgressPercentageAPIView

urlpatterns = [
    path('lessons/<int:lesson_id>/complete/', RecordLessonCompletionAPIView.as_view(), name='record-lesson-completion'),
    path('exercises/<int:exercise_id>/submit/', ExerciseSubmissionAPIView.as_view(), name='submit-exercise'),
    path('lessons/<int:lesson_id>/progress/', LessonProgressPercentageAPIView.as_view(), name='lesson-progress-percentage'),
]
