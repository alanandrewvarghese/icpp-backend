from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    QuizViewSet, QuestionViewSet, ChoiceViewSet,
    SubmitQuizView, QuizStatsView, QuizManagementView, QuizDetailView
)

# Create a router for viewsets with explicit basename
router = DefaultRouter()
router.register(r'quizzes', QuizViewSet, basename='quiz')  # Add basename explicitly
router.register(r'questions', QuestionViewSet)
router.register(r'choices', ChoiceViewSet)

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # Quiz submission endpoint
    path('submit/', SubmitQuizView.as_view(), name='quiz-submit'),

    # Quiz statistics endpoint
    path('quizzes/<int:quiz_id>/stats/', QuizStatsView.as_view(), name='quiz-stats'),

    # Register QuizManagementView (if you want to use this alternative)
    path('quiz_management/<int:quiz_id>/', QuizManagementView.as_view(), name='quiz-management'),

    # Add this line to register the QuizDetailView
    path('lesson/<int:lesson_id>/quiz/', QuizDetailView.as_view(), name='lesson-quiz'),
]
