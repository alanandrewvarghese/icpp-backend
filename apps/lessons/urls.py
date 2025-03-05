from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import LessonViewSet, ExerciseViewSet, lesson_exercises_list

router = DefaultRouter()
router.register(r'lessons', LessonViewSet, basename='lesson') # 'lessons/' endpoint for LessonViewSet
router.register(r'exercises', ExerciseViewSet, basename='exercise') # 'exercises/' endpoint for ExerciseViewSet

urlpatterns = [
    path('', include(router.urls)), # Include router URLs
    path('<int:lesson_id>/exercises/', lesson_exercises_list, name='lesson-exercises-list'),
]