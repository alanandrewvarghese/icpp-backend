from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from .models import Quiz, Question, Choice, QuizAttempt
from .serializers import QuizSerializer, QuestionSerializer, QuizAttemptSerializer, QuizSubmissionSerializer
from apps.lessons.models import Lesson
from apps.progress.models import LessonProgress
import logging

logger = logging.getLogger("quiz")

class QuizDetailView(APIView):
    """
    API view to retrieve a quiz for a specific lesson.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, lesson_id):
        try:
            lesson = Lesson.objects.get(pk=lesson_id)
            quiz = get_object_or_404(Quiz, lesson=lesson)
            serializer = QuizSerializer(quiz)
            return Response(serializer.data)
        except Lesson.DoesNotExist:
            logger.warning(f"Quiz requested for non-existent lesson ID: {lesson_id}")
            return Response({"error": "Lesson not found"}, status=status.HTTP_404_NOT_FOUND)
        except Quiz.DoesNotExist:
            logger.warning(f"No quiz found for lesson ID: {lesson_id}")
            return Response({"error": "No quiz available for this lesson"}, status=status.HTTP_404_NOT_FOUND)

class SubmitQuizView(APIView):
    """
    API view to handle quiz submissions and mark lesson as complete if passed.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = QuizSubmissionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        quiz_id = serializer.validated_data['quiz_id']
        answers = serializer.validated_data['answers']

        try:
            quiz = Quiz.objects.get(pk=quiz_id)
            lesson = quiz.lesson
            user = request.user

            # Calculate score
            total_questions = quiz.questions.count()
            if total_questions == 0:
                return Response(
                    {"error": "This quiz has no questions"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            correct_answers = 0
            for answer in answers:
                for question_id, choice_id in answer.items():
                    try:
                        question = Question.objects.get(pk=question_id, quiz=quiz)
                        if Choice.objects.filter(pk=choice_id, question=question, is_correct=True).exists():
                            correct_answers += 1
                    except (Question.DoesNotExist, Choice.DoesNotExist):
                        pass  # Skip invalid answers

            score = (correct_answers / total_questions) * 100
            passed = score >= quiz.passing_score

            # Record the attempt
            attempt = QuizAttempt.objects.create(
                user=user,
                quiz=quiz,
                score=score,
                passed=passed
            )

            # If passed, mark the lesson as complete
            if passed:
                # Create lesson progress only if it doesn't exist
                LessonProgress.objects.get_or_create(
                    user=user,
                    lesson=lesson
                )
                logger.info(f"User {user.username} passed quiz for lesson '{lesson.title}' with score {score}%")

                return Response({
                    "message": "Quiz passed successfully! Lesson marked as complete.",
                    "score": score,
                    "passed": True,
                    "attempt_id": attempt.id
                })
            else:
                logger.info(f"User {user.username} failed quiz for lesson '{lesson.title}' with score {score}%")
                return Response({
                    "message": "Quiz not passed. Please try again.",
                    "score": score,
                    "passed": False,
                    "attempt_id": attempt.id
                })

        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)
