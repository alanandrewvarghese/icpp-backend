from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Count, F, Q, Avg, ExpressionWrapper, FloatField, Sum, Case, When, Value
from django.db.models.functions import TruncDay
from django.contrib.auth import get_user_model
from apps.lessons.models import Lesson, Exercise
from apps.progress.models import LessonProgress, ExerciseSubmission
from apps.sandbox.models import ExecutionRequest, ExecutionResult
from apps.common.permissions import IsAdminOrInstructor
from .serializers import (
    LessonAnalyticsSerializer,
    ExerciseAnalyticsSerializer,
    SandboxAnalyticsSerializer,
    LessonStatsSerializer,
    LessonDetailSerializer,
    LessonTrendSerializer,
    ExerciseStatsSerializer,
    ExerciseDetailSerializer,
    ExerciseTrendSerializer,
    ErrorTypeSerializer,
    SandboxStatsSerializer,
    SandboxTrendSerializer,
    LanguageDistributionSerializer
)
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("analytics")

User = get_user_model()


class LessonAnalyticsAPIView(APIView):
    """
    API view for providing analytics data related to lessons and their completion rates.
    Requires admin or instructor permissions.
    """
    permission_classes = [IsAdminOrInstructor]

    def get(self, request):
        try:
            # Get basic counts
            total_lessons = Lesson.objects.count()
            total_students = User.objects.filter(role='student').count()

            # Calculate unique lesson completions (one per student per lesson)
            unique_completions = LessonProgress.objects.values('lesson', 'user').distinct().count()

            # Calculate overall completion percentage based on unique completions
            overall_completion_percentage = 0
            if total_lessons > 0 and total_students > 0:
                possible_completions = total_lessons * total_students
                overall_completion_percentage = (unique_completions / possible_completions) * 100 if possible_completions > 0 else 0

            # Get lesson completion data
            lesson_stats = []
            for lesson in Lesson.objects.all():
                # Count distinct students who completed this lesson
                completion_count = LessonProgress.objects.filter(lesson=lesson).values('user').distinct().count()

                # Prevent completion rate from exceeding 100%
                if completion_count > total_students:
                    logger.warning(f"Data anomaly: Lesson '{lesson.title}' (ID: {lesson.id}) has more completions ({completion_count}) than students ({total_students})")
                    completion_count = min(completion_count, total_students)

                completion_rate = (completion_count / total_students) * 100 if total_students > 0 else 0
                lesson_stats.append({
                    'id': lesson.id,
                    'title': lesson.title,
                    'completion_count': completion_count,
                    'completion_rate': round(completion_rate, 2),
                    'student_count': total_students
                })

            # Sort lessons by completion rate
            sorted_lessons = sorted(lesson_stats, key=lambda x: x['completion_rate'], reverse=True)
            top_completed_lessons = sorted_lessons[:5]  # Top 5
            lowest_completion_lessons = sorted_lessons[-5:] if len(sorted_lessons) >= 5 else sorted_lessons  # Bottom 5

            # Get trend data for the last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            trend_data = LessonProgress.objects.filter(
                completed_at__gte=thirty_days_ago
            ).annotate(
                day=TruncDay('completed_at')
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')

            # Prepare response data
            analytics_data = {
                'overall_stats': {
                    'total_lessons': total_lessons,
                    'total_students': total_students,
                    'total_completions': unique_completions,
                    'overall_completion_percentage': round(overall_completion_percentage, 2)
                },
                'top_completed_lessons': top_completed_lessons,
                'lowest_completion_lessons': lowest_completion_lessons,
                'completion_trend': [
                    {'day': item['day'], 'count': item['count']}
                    for item in trend_data
                ]
            }

            serializer = LessonAnalyticsSerializer(analytics_data)
            logger.info(f"Lesson analytics data retrieved successfully by user '{request.user.username}'")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Error generating lesson analytics: {str(e)}")
            return Response(
                {"error": "Failed to generate lesson analytics data.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExerciseAnalyticsAPIView(APIView):
    """
    API view for providing analytics data related to exercises and student performance.
    Requires admin or instructor permissions.
    """
    permission_classes = [IsAdminOrInstructor]

    def get(self, request):
        try:
            # Get basic counts - Adding total_students consistent with role-based filtering
            total_students = User.objects.filter(role='student').count()
            total_submissions = ExerciseSubmission.objects.count()
            correct_submissions = ExerciseSubmission.objects.filter(is_correct=True).count()
            incorrect_submissions = total_submissions - correct_submissions
            success_rate = (correct_submissions / total_submissions) * 100 if total_submissions > 0 else 0

            # Get exercise attempt data
            exercise_stats = []
            for exercise in Exercise.objects.all():
                total_attempts = ExerciseSubmission.objects.filter(exercise=exercise).count()
                correct_attempts = ExerciseSubmission.objects.filter(exercise=exercise, is_correct=True).count()
                ex_success_rate = (correct_attempts / total_attempts) * 100 if total_attempts > 0 else 0
                exercise_stats.append({
                    'id': exercise.id,
                    'title': exercise.title,
                    'total_attempts': total_attempts,
                    'correct_attempts': correct_attempts,
                    'success_rate': round(ex_success_rate, 2)
                })

            # Get most attempted exercises
            most_attempted = sorted(exercise_stats, key=lambda x: x['total_attempts'], reverse=True)[:5]

            # Get most challenging exercises (low success rate with significant attempts)
            challenging_exercises = sorted(
                [ex for ex in exercise_stats if ex['total_attempts'] >= 5],  # Only exercises with meaningful attempt counts
                key=lambda x: x['success_rate']
            )[:5]

            # Get trend data for the last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            trend_data = ExerciseSubmission.objects.filter(
                submitted_at__gte=thirty_days_ago
            ).annotate(
                day=TruncDay('submitted_at')
            ).values('day').annotate(
                total=Count('id'),
                correct=Sum(Case(When(is_correct=True, then=1), default=0)),
                incorrect=Sum(Case(When(is_correct=False, then=1), default=0))
            ).order_by('day')

            # Get common error types from execution results
            error_types = ExecutionResult.objects.filter(
                error__isnull=False,
                error__gt='',  # Non-empty error
                request__exercise__isnull=False  # Only for exercise attempts
            ).values(
                error_type=F('error')
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:5]

            # Prepare response data
            analytics_data = {
                'overall_stats': {
                    'total_submissions': total_submissions,
                    'correct_submissions': correct_submissions,
                    'incorrect_submissions': incorrect_submissions,
                    'success_rate': round(success_rate, 2),
                    'total_students': total_students  # Added for consistency
                },
                'most_attempted_exercises': most_attempted,
                'challenging_exercises': challenging_exercises,
                'submission_trend': [
                    {
                        'day': item['day'],
                        'total': item['total'],
                        'correct': item['correct'],
                        'incorrect': item['incorrect']
                    }
                    for item in trend_data
                ],
                'common_error_types': [
                    {
                        'error_type': item['error_type'][:100],  # Limit error text to reasonable length
                        'count': item['count']
                    }
                    for item in error_types
                ]
            }

            serializer = ExerciseAnalyticsSerializer(analytics_data)
            logger.info(f"Exercise analytics data retrieved successfully by user '{request.user.username}'")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Error generating exercise analytics: {str(e)}")
            return Response(
                {"error": "Failed to generate exercise analytics data.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SandboxAnalyticsAPIView(APIView):
    """
    API view for providing analytics data related to code execution in the sandbox environment.
    Requires admin or instructor permissions.
    """
    permission_classes = [IsAdminOrInstructor]

    def get(self, request):
        try:
            # Get basic counts
            total_executions = ExecutionRequest.objects.count()
            successful_executions = ExecutionRequest.objects.filter(status='completed').count()
            failed_executions = ExecutionRequest.objects.filter(status='failed').count()
            success_rate = (successful_executions / total_executions) * 100 if total_executions > 0 else 0

            # Calculate average execution time if available - Fixed to safely check for field existence
            avg_execution_time = None
            try:
                # Check if the field exists in the model, not just as a property
                if ExecutionResult.objects.exists() and hasattr(ExecutionResult, 'execution_time'):
                    # Check if it's a database field, not just an attribute
                    if 'execution_time' in [f.name for f in ExecutionResult._meta.get_fields()]:
                        avg_execution_time = ExecutionResult.objects.aggregate(
                            avg_time=Avg('execution_time')
                        )['avg_time']
            except Exception as field_error:
                logger.warning(f"Error accessing execution_time field: {str(field_error)}")
                # Continue without the average time

            # Get trend data for the last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            trend_data = ExecutionRequest.objects.filter(
                created_at__gte=thirty_days_ago
            ).annotate(
                day=TruncDay('created_at')
            ).values('day').annotate(
                total=Count('id'),
                successful=Sum(Case(When(status='completed', then=1), default=0)),
                failed=Sum(Case(When(status='failed', then=1), default=0))
            ).order_by('day')

            # Get common error types from execution results
            error_types = ExecutionResult.objects.filter(
                error__isnull=False,
                error__gt=''  # Non-empty error
            ).values(
                error_type=F('error')
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:5]

            # Get language distribution - Fixed to safely check field existence
            language_distribution = []
            try:
                # Check if language field exists on ExecutionRequest model
                if 'language' in [f.name for f in ExecutionRequest._meta.get_fields()]:
                    language_distribution = ExecutionRequest.objects.values(
                        language=F('language')
                    ).annotate(
                        count=Count('id')
                    ).order_by('-count')
                else:
                    # Placeholder for Python if language field doesn't exist
                    language_distribution = [{'language': 'Python', 'count': total_executions}]
            except Exception as field_error:
                logger.warning(f"Error accessing language field: {str(field_error)}")
                # Default to Python as fallback
                language_distribution = [{'language': 'Python', 'count': total_executions}]

            # Prepare response data
            analytics_data = {
                'overall_stats': {
                    'total_executions': total_executions,
                    'successful_executions': successful_executions,
                    'failed_executions': failed_executions,
                    'success_rate': round(success_rate, 2),
                    'avg_execution_time_seconds': round(avg_execution_time, 3) if avg_execution_time else None
                },
                'execution_trend': [
                    {
                        'day': item['day'],
                        'total': item['total'],
                        'successful': item['successful'],
                        'failed': item['failed']
                    }
                    for item in trend_data
                ],
                'common_error_types': [
                    {
                        'error_type': item['error_type'][:100],  # Limit error text to reasonable length
                        'count': item['count']
                    }
                    for item in error_types
                ],
                'language_distribution': language_distribution
            }

            serializer = SandboxAnalyticsSerializer(analytics_data)
            logger.info(f"Sandbox analytics data retrieved successfully by user '{request.user.username}'")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Error generating sandbox analytics: {str(e)}")
            return Response(
                {"error": "Failed to generate sandbox analytics data.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
