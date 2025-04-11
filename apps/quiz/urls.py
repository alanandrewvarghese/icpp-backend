from django.urls import path
from .api_views import QuizDetailView, SubmitQuizView

urlpatterns = [
    path('lessons/<int:lesson_id>/quiz/', QuizDetailView.as_view(), name='quiz-detail'),
    path('submit/', SubmitQuizView.as_view(), name='quiz-submit'),
]
