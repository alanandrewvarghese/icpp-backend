from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import LessonProgressSerializer, ExerciseSubmissionSerializer, LessonProgressPercentageSerializer
from .models import LessonProgress, ExerciseSubmission
from apps.lessons.models import Lesson, Exercise
from apps.sandbox.api_views import ExecutionRequestAPIView
from apps.sandbox.models import ExecutionResult
from apps.sandbox.serializers import ExecutionRequestSerializer, ExecutionResultSerializer
from rest_framework.test import APIRequestFactory, force_authenticate
from django.test import RequestFactory
from rest_framework.test import force_authenticate
from rest_framework.request import Request
from .utils import send_execution_request
import logging

logger = logging.getLogger("progress")


class RecordLessonCompletionAPIView(APIView):
    """
    API view to record when a user completes a lesson.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, lesson_id):
        try:
            lesson = Lesson.objects.get(pk=lesson_id)
        except Lesson.DoesNotExist:
            logger.warning(f"RecordLessonCompletionAPIView: Lesson with ID '{lesson_id}' not found.")
            return Response({"error": "Lesson not found."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        # Check if progress already recorded to avoid duplicates
        if LessonProgress.objects.filter(user=user, lesson=lesson).exists():
            logger.info(f"Lesson progress already recorded for user '{user.username}' and lesson '{lesson.title}'.")
            return Response({"message": "Lesson progress already recorded."}, status=status.HTTP_200_OK)

        # Check if the user has completed at least 3 unique exercises for the lesson
        completed_exercises_count = ExerciseSubmission.objects.filter(user=user, exercise__lesson=lesson, is_correct=True).values('exercise').distinct().count()
        if completed_exercises_count < 3:
            logger.info(f"User '{user.username}' has not completed enough exercises for lesson '{lesson.title}'.")
            return Response({"message": "Complete 3 exercises before proceeding."}, status=status.HTTP_200_OK)

        progress_data = {'user': user.id, 'lesson': lesson.id} # Data to serialize
        serializer = LessonProgressSerializer(data=progress_data) # Create serializer instance

        if serializer.is_valid(): # Validate data
            serializer.save(user=user, lesson=lesson) # Save the progress record
            logger.info(f"Lesson progress recorded for user '{user.username}' and lesson '{lesson.title}'.")
            return Response(serializer.data, status=status.HTTP_201_CREATED) # Return success response
        else:
            logger.warning(f"RecordLessonCompletionAPIView: Invalid data for lesson completion by user '{user.username}'. Errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) # Return error response

class ExerciseSubmissionAPIView(APIView):
    """
    API view to handle student submissions for exercises, trigger code execution, and check tests.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, exercise_id):
        try:
            exercise = Exercise.objects.get(pk=exercise_id)
        except Exercise.DoesNotExist:
            logger.warning(f"Exercise with ID '{exercise_id}' not found.")
            return Response({"error": "Exercise not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ExerciseSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(
                f"Invalid submission data from user '{request.user.username}' for exercise '{exercise.title}'. Errors: {serializer.errors}"
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Save initial submission
        submission = serializer.save(user=request.user, exercise=exercise)
        logger.debug(f"Received execution request data: {request.data}")

        # --- Prepare Code Execution Request ---
        execution_request_data = {
            "exercise": exercise.id,
            "code": serializer.validated_data.get("submitted_code", 'print("404")'),
            "sandbox": exercise.sandbox,
            "stdin": "",
        }

        execution_serializer = ExecutionRequestSerializer(data=execution_request_data)
        if not execution_serializer.is_valid():
            logger.warning(f"Invalid execution request data for submission ID {submission.id}. Errors: {execution_serializer.errors}")
            submission.delete()
            return Response(
                {"error": "Invalid submission data for code execution.", "details": execution_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        execution_request = execution_serializer.save(user=request.user)

        # --- Extract & Validate JWT Token ---
        auth_header = request.headers.get("Authorization", "")
        jwt_token = None
        if auth_header.startswith("Bearer "):
            jwt_token = auth_header.split("Bearer ")[-1]

        if not jwt_token:
            logger.error("JWT token missing or invalid.")
            submission.delete()
            return Response({"error": "Authentication token missing."}, status=status.HTTP_401_UNAUTHORIZED)

        # --- Send Execution Request ---
        execution_response = send_execution_request(execution_request_data, token=jwt_token)
        logger.debug(f"ExecutionResponse: {execution_response}")

        # Check if execution_response is a dictionary (not a Response object)
        if isinstance(execution_response, dict):
            # Handle as dictionary response
            status_code = execution_response.get('status_code', 201)

            # Check if the execution was successful (201 Created)
            if status_code == status.HTTP_201_CREATED:
                execution_result_data = execution_response
                logger.debug(f"ExecutionResultData: {execution_result_data}")

                execution_result_serializer = ExecutionResultSerializer(data=execution_result_data)

                if execution_result_serializer.is_valid():
                    execution_result_id = execution_result_data.get('id')
                    if execution_result_id:
                        execution_result = ExecutionResult.objects.get(pk=execution_result_id)

                        submission.execution_result = execution_result
                        submission.save()

                        # --- Check Test Cases and Update is_correct ---
                        test_results = execution_result.test_results or []
                        all_tests_passed = all(result.get('passed', False) for result in test_results)
                        submission.is_correct = all_tests_passed
                        submission.save()

                        logger.info(f"Exercise submission processed for user '{request.user.username}', exercise '{exercise.title}'. Submission ID: {submission.id}, Execution Result ID: {execution_result.id}, Tests Passed: {all_tests_passed}")
                        initial_serializer = ExerciseSubmissionSerializer(submission)
                        response_data = initial_serializer.data
                        response_data['is_correct'] = submission.is_correct
                        response_data['execution_result'] = execution_result.id
                        return Response(response_data, status=status.HTTP_201_CREATED)
                    else:
                        logger.error(f"Execution result ID not found in execution response for submission ID {submission.id}.")
                        submission.delete()
                        return Response({"error": "Failed to retrieve execution result ID from sandbox response."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    logger.error(f"Error serializing ExecutionResult for submission ID {submission.id}. Errors: {execution_result_serializer.errors}")
                    submission.delete()
                    return Response({"error": "Failed to process execution result.", "details": execution_result_serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                logger.error(f"Execution request failed for submission ID {submission.id}. Sandbox response: {execution_response}")
                submission.delete()
                return Response({"error": "Code execution failed.", "details": execution_response}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Handle as Response object (original code path)
            if execution_response.status_code == status.HTTP_201_CREATED:
                execution_result_data = execution_response.data
                execution_result_serializer = ExecutionResultSerializer(data=execution_result_data)
                if execution_result_serializer.is_valid():
                    execution_result_id = execution_response.data.get('id')
                    if execution_result_id:
                        execution_result = ExecutionResult.objects.get(pk=execution_result_id)

                        submission.execution_result = execution_result
                        submission.save()

                        # --- Check Test Cases and Update is_correct ---
                        test_results = execution_result.test_results or []
                        all_tests_passed = all(result.get('passed', False) for result in test_results)
                        submission.is_correct = all_tests_passed
                        submission.save()

                        logger.info(f"Exercise submission processed for user '{request.user.username}', exercise '{exercise.title}'. Submission ID: {submission.id}, Execution Result ID: {execution_result.id}, Tests Passed: {all_tests_passed}")
                        initial_serializer = ExerciseSubmissionSerializer(submission)
                        response_data = initial_serializer.data
                        response_data['is_correct'] = submission.is_correct
                        response_data['execution_result'] = execution_result.id
                        return Response(response_data, status=status.HTTP_201_CREATED)
                    else:
                        logger.error(f"Execution result ID not found in execution response for submission ID {submission.id}.")
                        submission.delete()
                        return Response({"error": "Failed to retrieve execution result ID from sandbox response."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    logger.error(f"Error serializing ExecutionResult for submission ID {submission.id}. Errors: {execution_result_serializer.errors}")
                    submission.delete()
                    return Response({"error": "Failed to process execution result.", "details": execution_result_serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                logger.error(f"Execution request failed for submission ID {submission.id}. Sandbox response status: {execution_response.status_code}, data: {execution_response.data}")
                submission.delete()
                return Response({"error": "Code execution failed.", "details": execution_response.data}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LessonProgressPercentageAPIView(APIView):
    """
    API view to retrieve the percentage of exercises completed for a lesson.
    Returns the progress as a percentage and detailed stats about completed exercises.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, lesson_id):
        try:
            lesson = Lesson.objects.get(pk=lesson_id)
        except Lesson.DoesNotExist:
            logger.warning(f"LessonProgressPercentageAPIView: Lesson with ID '{lesson_id}' not found.")
            return Response({"error": "Lesson not found."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        total_exercises = Exercise.objects.filter(lesson=lesson).count()

        if total_exercises == 0:
            data = {
                "lesson_id": lesson_id,
                "lesson_title": lesson.title,
                "progress_percentage": 0,
                "completed_exercises": 0,
                "total_exercises": 0,
                "is_completed": False
            }
            serializer = LessonProgressPercentageSerializer(data)
            logger.info(f"No exercises found for lesson '{lesson.title}'.")
            return Response(serializer.data, status=status.HTTP_200_OK)

        completed_exercises = ExerciseSubmission.objects.filter(
            user=user,
            exercise__lesson=lesson,
            is_correct=True
        ).values('exercise').distinct().count()

        progress_percentage = (completed_exercises / total_exercises) * 100

        lesson_completed = LessonProgress.objects.filter(user=user, lesson=lesson).exists()

        progress_data = {
            "lesson_id": lesson_id,
            "lesson_title": lesson.title,
            "progress_percentage": round(progress_percentage, 2),
            "completed_exercises": completed_exercises,
            "total_exercises": total_exercises,
            "is_completed": lesson_completed
        }

        serializer = LessonProgressPercentageSerializer(progress_data)
        logger.info(f"Calculated progress for user '{user.username}' on lesson '{lesson.title}': {progress_percentage:.2f}%")
        return Response(serializer.data, status=status.HTTP_200_OK)
