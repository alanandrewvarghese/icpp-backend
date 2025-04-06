from django.urls import path
from .api_views import (
    LessonAnalyticsAPIView,
    ExerciseAnalyticsAPIView,
    SandboxAnalyticsAPIView
)

urlpatterns = [
    path('lessons/', LessonAnalyticsAPIView.as_view(), name='lesson-analytics'),
    path('exercises/', ExerciseAnalyticsAPIView.as_view(), name='exercise-analytics'),
    path('sandbox/', SandboxAnalyticsAPIView.as_view(), name='sandbox-analytics'),
]
