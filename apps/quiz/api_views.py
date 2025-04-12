from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from django.shortcuts import get_object_or_404
from django.db import models
from .models import Quiz, Question, Choice, QuizAttempt
from .serializers import QuizSerializer, QuestionSerializer, ChoiceSerializer, QuizAttemptSerializer, QuizSubmissionSerializer
from apps.lessons.models import Lesson
from apps.progress.models import LessonProgress
from apps.common.permissions import IsAdminOrInstructor
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

# Modify QuizViewSet to add custom actions
class QuizViewSet(viewsets.ModelViewSet):
    """
    API viewset for quiz CRUD operations.

    GET /api/quiz/quizzes/ - List all quizzes (instructors see only their own)
    GET /api/quiz/quizzes/{id}/ - Get details for a specific quiz
    POST /api/quiz/quizzes/ - Create a new quiz
    PUT/PATCH /api/quiz/quizzes/{id}/ - Update a quiz
    DELETE /api/quiz/quizzes/{id}/ - Delete a quiz
    GET /api/quiz/quizzes/for_lesson/{lesson_id}/ - Get quiz for a specific lesson
    POST /api/quiz/quizzes/bulk_update/{id}/ - Bulk update quiz questions and choices
    """
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        Override to ensure only admins/instructors can create, edit, delete quizzes
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdminOrInstructor()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Add the current user as creator when creating a quiz"""
        serializer.save(created_by=self.request.user)
        logger.info(f"Quiz '{serializer.instance.title}' created by {self.request.user.username}")

    def perform_update(self, serializer):
        """Log quiz updates"""
        serializer.save()
        logger.info(f"Quiz '{serializer.instance.title}' updated by {self.request.user.username}")

    def perform_destroy(self, instance):
        """Log quiz deletion"""
        title = instance.title
        super().perform_destroy(instance)
        logger.info(f"Quiz '{title}' deleted by {self.request.user.username}")

    def get_queryset(self):
        """
        Filter quizzes for instructors to only show their own quizzes
        """
        if self.request.user.role == 'instructor':
            return Quiz.objects.filter(created_by=self.request.user)
        return super().get_queryset()

    @action(detail=False, methods=['get'], url_path='for_lesson/(?P<lesson_id>[^/.]+)')
    def for_lesson(self, request, lesson_id=None):
        """Get quiz for a specific lesson"""
        try:
            lesson = get_object_or_404(Lesson, pk=lesson_id)
            quiz = get_object_or_404(Quiz, lesson=lesson)
            serializer = self.get_serializer(quiz)
            return Response(serializer.data)
        except Lesson.DoesNotExist:
            logger.warning(f"Quiz requested for non-existent lesson ID: {lesson_id}")
            return Response({"error": "Lesson not found"}, status=status.HTTP_404_NOT_FOUND)
        except Quiz.DoesNotExist:
            logger.warning(f"No quiz found for lesson ID: {lesson_id}")
            return Response({"error": "No quiz available for this lesson"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='bulk_update')
    def bulk_update(self, request, pk=None):
        """Bulk update questions and choices for a quiz"""
        quiz = self.get_object()

        # Fix the permission logic to correctly handle instructors
        if request.user.role == 'instructor' and quiz.created_by != request.user:
            logger.warning(f"Permission denied: User {request.user} (role: {request.user.role}) attempted to update quiz {quiz.id} created by {quiz.created_by}")
            return Response(
                {"error": "You don't have permission to update this quiz"},
                status=status.HTTP_403_FORBIDDEN
            )

        questions_data = request.data.get('questions', [])

        # Update or create questions and their choices
        for question_data in questions_data:
            question_id = question_data.get('id')
            choices_data = question_data.pop('choices', [])

            if question_id:
                # Update existing question
                question = get_object_or_404(Question, id=question_id, quiz=quiz)
                question_serializer = QuestionSerializer(question, data=question_data, partial=True)
            else:
                # Create new question
                question_data['quiz'] = quiz.id
                question_serializer = QuestionSerializer(data=question_data)

            if question_serializer.is_valid():
                question = question_serializer.save()

                # Process choices for this question
                for choice_data in choices_data:
                    choice_id = choice_data.get('id')

                    if choice_id:
                        # Update existing choice
                        choice = get_object_or_404(Choice, id=choice_id, question=question)
                        choice_serializer = ChoiceSerializer(choice, data=choice_data, partial=True)
                    else:
                        # Create new choice
                        choice_data['question'] = question.id
                        choice_serializer = ChoiceSerializer(data=choice_data)

                    if choice_serializer.is_valid():
                        choice_serializer.save()
                    else:
                        return Response(choice_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(question_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Return the updated quiz with all questions and choices
        serializer = self.get_serializer(quiz)
        return Response(serializer.data)

class QuestionViewSet(viewsets.ModelViewSet):
    """
    API viewset for quiz questions CRUD operations.
    """
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    # Temporarily comment this out for testing
    # permission_classes = [permissions.IsAuthenticated, IsAdminOrInstructor]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filter questions by quiz if quiz_id is provided
        quiz_id = self.request.query_params.get('quiz_id')
        queryset = super().get_queryset()

        # Filter based on role
        if self.request.user.role == 'instructor':
            # Instructors can only access questions for quizzes they created
            queryset = queryset.filter(quiz__created_by=self.request.user)

        # Apply quiz filter if provided
        if quiz_id:
            queryset = queryset.filter(quiz_id=quiz_id).order_by('order')

        return queryset

    def perform_create(self, serializer):
        # Get the quiz to check for permission
        quiz_id = self.request.data.get('quiz')
        quiz = get_object_or_404(Quiz, id=quiz_id)

        # Check if instructor has permission for this quiz
        if self.request.user.role == 'instructor' and quiz.created_by != self.request.user:
            raise permissions.exceptions.PermissionDenied("You don't have permission to add questions to this quiz")

        # Automatically set the next order if not provided
        if 'order' not in self.request.data or not self.request.data['order']:
            max_order = Question.objects.filter(quiz=quiz).aggregate(models.Max('order'))['order__max'] or 0
            serializer.save(order=max_order + 1)
        else:
            serializer.save()

        logger.info(f"Question added to quiz '{quiz.title}' by {self.request.user.username}")

    def perform_update(self, serializer):
        # Get the question instance that's being updated
        question = self.get_object()
        quiz = question.quiz
        user = self.request.user

        # Enhanced debugging logs
        logger.info(f"Question update attempt - Details:")
        logger.info(f"  • User ID: {user.id}, Username: {user.username}")
        logger.info(f"  • User role: {getattr(user, 'role', 'No role attribute')}")
        logger.info(f"  • Quiz ID: {quiz.id}, Title: '{quiz.title}'")
        logger.info(f"  • Quiz creator ID: {quiz.created_by.id if quiz.created_by else 'None'}")
        logger.info(f"  • Creator username: {quiz.created_by.username if quiz.created_by else 'None'}")
        logger.info(f"  • Permission check: user.role=='instructor'? {user.role == 'instructor'}")
        logger.info(f"  • Permission check: Different creator? {quiz.created_by != user}")

        # Check if instructor has permission for this quiz
        if user.role == 'instructor' and quiz.created_by != user:
            logger.warning(f"Permission denied: User {user.username} (role: {user.role}) tried to update question {question.id} for quiz created by {quiz.created_by.username if quiz.created_by else 'None'}")
            raise permissions.exceptions.PermissionDenied("You don't have permission to update questions for this quiz")

        # Proceed with the update if permission check passes
        serializer.save()
        logger.info(f"Question {question.id} updated successfully in quiz '{quiz.title}' by {user.username}")

class ChoiceViewSet(viewsets.ModelViewSet):
    """
    API viewset for question choices CRUD operations.
    """
    queryset = Choice.objects.all()
    serializer_class = ChoiceSerializer
    # permission_classes = [permissions.IsAuthenticated, IsAdminOrInstructor]
    permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self):
        # Filter choices by question if question_id is provided
        question_id = self.request.query_params.get('question_id')
        queryset = super().get_queryset()

        # Filter based on role
        if self.request.user.role == 'instructor':
            # Instructors can only access choices for questions in quizzes they created
            queryset = queryset.filter(question__quiz__created_by=self.request.user)

        # Apply question filter if provided
        if question_id:
            queryset = queryset.filter(question_id=question_id)

        return queryset

    def perform_create(self, serializer):
        question_id = self.request.data.get('question')
        question = get_object_or_404(Question, id=question_id)

        # Check if instructor has permission for this question's quiz
        if self.request.user.role == 'instructor' and question.quiz.created_by != self.request.user:
            raise permissions.exceptions.PermissionDenied("You don't have permission to add choices to this question")

        serializer.save()
        logger.info(f"Choice added to question in quiz '{question.quiz.title}' by {self.request.user.username}")

    def perform_update(self, serializer):
        # Start with a clear marker in the logs
        logger.warning("=== CHOICE UPDATE ATTEMPT STARTED ===")

        try:
            # Get the choice instance that's being updated
            choice = self.get_object()
            question = choice.question
            quiz = question.quiz
            user = self.request.user

            # Detailed user information
            logger.warning(f"User details: ID={user.id}, username={user.username}, role={getattr(user, 'role', 'unknown')}")

            # Object relationship information
            logger.warning(f"Object hierarchy: Choice(id={choice.id}) → Question(id={question.id}) → Quiz(id={quiz.id}, title='{quiz.title}')")

            # Creator information with null check
            creator_id = quiz.created_by.id if quiz.created_by else 'None'
            creator_name = quiz.created_by.username if quiz.created_by else 'None'
            logger.warning(f"Quiz creator: ID={creator_id}, username={creator_name}")

            # Important comparison logic that might be failing
            is_instructor = user.role == 'instructor'
            is_not_creator = quiz.created_by != user
            logger.warning(f"Permission check components: is_instructor={is_instructor}, is_not_creator={is_not_creator}")
            logger.warning(f"Full permission check: {is_instructor and is_not_creator}")

            # Object ID comparison that might be failing
            if quiz.created_by:
                logger.warning(f"ID comparison: user.id={user.id}, quiz.created_by.id={quiz.created_by.id}, equal?={user.id == quiz.created_by.id}")

            # Check if instructor has permission for this quiz
            if user.role == 'instructor' and quiz.created_by != user:
                logger.warning(f"PERMISSION DENIED: Instructor {user.username} (id={user.id}) cannot update choice in quiz created by {creator_name} (id={creator_id})")
                raise permissions.exceptions.PermissionDenied("You don't have permission to update choices for this question")

            # Log successful permission check
            logger.warning(f"Permission check PASSED. Proceeding with update.")

            # Proceed with the update if permission check passes
            serializer.save()
            logger.warning(f"Choice {choice.id} updated SUCCESSFULLY by {user.username}")

        except Exception as e:
            # Catch any exceptions to ensure they're logged
            logger.error(f"Error during choice update: {str(e)}", exc_info=True)
            raise

        finally:
            # End marker for this operation
            logger.warning("=== CHOICE UPDATE ATTEMPT ENDED ===")

class QuizManagementView(APIView):
    """
    API view for additional quiz management operations.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrInstructor]


    def post(self, request, lesson_id):
        """Create a new quiz for a lesson"""
        try:
            lesson = Lesson.objects.get(pk=lesson_id)

            # Check if a quiz already exists for this lesson
            if Quiz.objects.filter(lesson=lesson).exists():
                return Response(
                    {"error": "A quiz already exists for this lesson"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create a new quiz
            data = request.data
            data['lesson'] = lesson.id

            serializer = QuizSerializer(data=data)
            if serializer.is_valid():
                quiz = serializer.save(created_by=request.user)
                logger.info(f"New quiz '{quiz.title}' created for lesson '{lesson.title}' by {request.user.username}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Lesson.DoesNotExist:
            return Response(
                {"error": "Lesson not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, quiz_id):
        """Bulk update questions and choices for a quiz"""
        try:
            quiz = Quiz.objects.get(pk=quiz_id)

            # Check if instructor has permission to update this quiz
            if request.user.role == 'instructor' and quiz.created_by != request.user:
                return Response(
                    {"error": "You don't have permission to update this quiz"},
                    status=status.HTTP_403_FORBIDDEN
                )

            questions_data = request.data.get('questions', [])

            # Update or create questions and their choices
            for question_data in questions_data:
                question_id = question_data.get('id')
                choices_data = question_data.pop('choices', [])

                if question_id:
                    # Update existing question
                    question = get_object_or_404(Question, id=question_id, quiz=quiz)
                    question_serializer = QuestionSerializer(question, data=question_data, partial=True)
                else:
                    # Create new question
                    question_data['quiz'] = quiz.id
                    question_serializer = QuestionSerializer(data=question_data)

                if question_serializer.is_valid():
                    question = question_serializer.save()

                    # Process choices for this question
                    for choice_data in choices_data:
                        choice_id = choice_data.get('id')

                        if choice_id:
                            # Update existing choice
                            choice = get_object_or_404(Choice, id=choice_id, question=question)
                            choice_serializer = ChoiceSerializer(choice, data=choice_data, partial=True)
                        else:
                            # Create new choice
                            choice_data['question'] = question.id
                            choice_serializer = ChoiceSerializer(data=choice_data)

                        if choice_serializer.is_valid():
                            choice_serializer.save()
                        else:
                            return Response(choice_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response(question_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Return the updated quiz with all questions and choices
            serializer = QuizSerializer(quiz)
            return Response(serializer.data)

        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)

class QuizStatsView(APIView):
    """
    API view for quiz statistics.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminOrInstructor]

    def get(self, request, quiz_id):
        """Get statistics for a specific quiz"""
        try:
            quiz = Quiz.objects.get(pk=quiz_id)

            # Check if instructor has permission to view stats for this quiz
            if request.user.role == 'instructor' and quiz.created_by != request.user:
                return Response(
                    {"error": "You don't have permission to view statistics for this quiz"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Get total attempts
            total_attempts = QuizAttempt.objects.filter(quiz=quiz).count()

            # Get passing attempts
            passing_attempts = QuizAttempt.objects.filter(quiz=quiz, passed=True).count()

            # Calculate average score
            avg_score = QuizAttempt.objects.filter(quiz=quiz).aggregate(models.Avg('score'))['score__avg'] or 0

            # Get unique users who attempted
            unique_users = QuizAttempt.objects.filter(quiz=quiz).values('user').distinct().count()

            return Response({
                'quiz_id': quiz_id,
                'quiz_title': quiz.title,
                'total_attempts': total_attempts,
                'passing_attempts': passing_attempts,
                'pass_rate': (passing_attempts / total_attempts * 100) if total_attempts > 0 else 0,
                'avg_score': round(avg_score, 2),
                'unique_users': unique_users
            })

        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND)
