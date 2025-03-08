from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import ExecutionRequestSerializer, ExecutionResultSerializer
from .models import ExecutionRequest, ExecutionResult
from apps.lessons.models import Exercise
import logging
import requests  # To make HTTP requests to Piston API (Not directly used anymore, but might be implicitly used by utils)
import json  # To handle JSON data (Not directly used anymore, but might be implicitly used by utils)
from .utils import create_execution_result, execute_piston, execute_custom_sandbox # Import utility functions

logger = logging.getLogger("sandbox")


class ExecutionRequestAPIView(APIView):
    """
    API view to create a new ExecutionRequest and execute code using either Piston API or custom sandbox.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ExecutionRequestSerializer(data=request.data)
        if serializer.is_valid():
            execution_request = serializer.save(user=request.user)
            logger.info(f"Execution request created by user '{request.user.username}' with ID '{execution_request.id}', sandbox: '{execution_request.sandbox}'.")

            current_exercise = execution_request.exercise
            sandbox_type = current_exercise.sandbox if current_exercise else 'piston' # Default to piston if no exercise

            if sandbox_type != 'custom':
                sandbox_type = "piston"

            compile_output = "" # Initialize compile output and error
            compile_error = ""
            run_output = ""
            run_error = ""
            execution_success = True # Flag to track execution success
            error_message = "" # Initialize error message
            test_case_results = [] # Initialize test_case_results here, outside conditional block


            # Standard Code Execution (Always Perform)
            if sandbox_type == 'piston':
                compile_output, compile_error, run_output, run_error = execute_piston(execution_request) # Standard execution
                if compile_output is None and compile_error is None and run_output is None and run_error is None:
                    execution_success = False
                    error_message = "Failed to execute code with Piston API (standard execution)."
                else:
                    run_output = run_output 

            elif sandbox_type == 'custom':
                compile_output, compile_error, run_output, run_error = execute_custom_sandbox(execution_request) # Standard execution
                if compile_output is None and compile_error is None and run_output is None and run_error is None:
                    execution_success = False
                    error_message = "Failed to execute code with Custom Sandbox API (standard execution)."
                else:
                    run_output = run_output
            else:
                execution_success = False
                error_message = f"Invalid sandbox type specified: '{sandbox_type}'."


            # Test Case Execution Loop (Conditional - only if test cases are present)
            test_cases = []
            if current_exercise:
                test_cases = current_exercise.test_cases
                logger.debug(f"Retrieved test cases for exercise '{current_exercise.title}': {test_cases}")


                if test_cases: # Only execute test cases if they exist
                    logger.debug(f"Starting test case execution loop for request ID '{execution_request.id}'.")
                    for test_case in test_cases:
                        test_input = test_case.get("input", "")
                        expected_output = test_case.get("expected_output", "")
                        logger.debug(f"Executing test case: Input='{test_input}', Expected Output='{expected_output}'")

                        if sandbox_type == 'piston':
                            test_compile_output, test_compile_error, test_run_output, test_run_error = execute_piston(execution_request, test_input=test_input)
                            actual_output = test_run_output
                        elif sandbox_type == 'custom':
                            test_compile_output, test_compile_error, test_run_output, test_run_error = execute_custom_sandbox(execution_request, test_input=test_input)
                            actual_output = test_run_output
                        else:
                            actual_output = "Sandbox type error"
                            test_run_error = f"Invalid sandbox type: {sandbox_type}"

                        passed = False
                        if not test_run_error and actual_output.strip() == expected_output.strip():
                            passed = True

                        test_case_result = {
                            "test_case": test_case,
                            "actual_output": actual_output.strip(),
                            "passed": passed,
                            "error": test_run_error.strip() if test_run_error else ""
                        }
                        test_case_results.append(test_case_result)
                        logger.debug(f"Test case result: {test_case_result}")

                    logger.debug(f"Test case execution loop completed for request ID '{execution_request.id}'. Total test cases: {len(test_case_results)}")


            if execution_success: # Process result only if execution was successful in calling API
                execution_result = create_execution_result(
                    execution_request,
                    compile_output,
                    compile_error,
                    run_output,
                    run_error,
                    test_results=test_case_results if test_cases else None # Pass test_results conditionally
                )

                if compile_error:
                    execution_request.status = 'failed'
                    logger.warning(f"Piston execution request ID '{execution_request.id}' failed due to compile error: {compile_error}")
                elif run_error:
                    execution_request.status = 'failed'
                    logger.warning(f"Sandbox execution request ID '{execution_request.id}' failed due to runtime error: {run_error}")
                elif test_cases and not all(result['passed'] for result in test_case_results): # Check test case failures
                    execution_request.status = 'failed'
                    logger.warning(f"Execution request ID '{execution_request.id}' failed because one or more test cases failed.")
                else:
                    execution_request.status = 'completed'
                    logger.info(f"Sandbox execution request ID '{execution_request.id}' completed successfully.")

                execution_request.save()
                result_serializer = ExecutionResultSerializer(execution_result)
                return Response(result_serializer.data, status=status.HTTP_201_CREATED)

            else: # Handle overall execution failures
                execution_request.status = 'failed'
                execution_request.save()
                execution_result = ExecutionResult.objects.create(
                    request=execution_request,
                    output="Execution failed.",
                    error=error_message
                )
                result_serializer = ExecutionResultSerializer(execution_result)
                logger.error(f"Execution request ID '{execution_request.id}' failed: {error_message}")
                return Response(result_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else: # Handle serializer validation errors
            logger.warning(f"Invalid execution request data from user '{request.user.username}': {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExecutionResultAPIView(APIView):
    """
    API view to retrieve the ExecutionResult for a given ExecutionRequest ID.
    """
    permission_classes = [permissions.IsAuthenticated]  # Only authenticated users can retrieve results

    def get(self, request, request_id, *args, **kwargs):
        try:
            execution_request = ExecutionRequest.objects.get(pk=request_id)
            # Ensure that the user requesting the result is the same user who made the request, or an admin/instructor (if needed)
            if execution_request.user != request.user:  # Basic authorization: only the requester can see the result for now
                logger.warning(f"User '{request.user.username}' attempted to access execution result for request ID '{request_id}' belonging to another user.")
                return Response({"error": "Unauthorized access."}, status=status.HTTP_403_FORBIDDEN)

            execution_result = ExecutionResult.objects.get(request=execution_request)  # Get the associated ExecutionResult
            serializer = ExecutionResultSerializer(execution_result)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ExecutionRequest.DoesNotExist:
            logger.warning(f"Execution request with ID '{request_id}' not found.")
            return Response({"error": "Execution request not found."}, status=status.HTTP_404_NOT_FOUND)
        except ExecutionResult.DoesNotExist:
            logger.warning(f"Execution result not found for request ID '{request_id}'. Result might still be pending.")
            return Response({"error": "Execution result not yet available."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(f"Error retrieving execution result for request ID '{request_id}': {e}")
            return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)