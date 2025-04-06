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
        logger.debug("ExecutionRequestAPIView: post - START") # Log start of ExecutionRequestAPIView

        # Check if there's an existing execution request ID
        existing_request_id = request.data.get('existing_request_id')

        if existing_request_id:
            try:
                execution_request = ExecutionRequest.objects.get(id=existing_request_id)
                logger.debug(f"Using existing execution request with ID: {existing_request_id}")
            except ExecutionRequest.DoesNotExist:
                logger.warning(f"Execution request with ID {existing_request_id} not found, creating new one")
                execution_request = None
        else:
            execution_request = None

        # If no existing request found or provided, create a new one
        if not execution_request:
            serializer = ExecutionRequestSerializer(data=request.data)
            if serializer.is_valid():
                logger.debug("ExecutionRequestAPIView: ExecutionRequestSerializer is valid") # Log serializer validation
                logger.debug("ExecutionRequestAPIView: Before serializer.save()") # Log before save
                execution_request = serializer.save(user=request.user)
                logger.info(f"Execution request created by user '{request.user.username}' with ID '{execution_request.id}', sandbox: '{execution_request.sandbox}'.")
                logger.debug(f"ExecutionRequestAPIView: ExecutionRequest saved with id={execution_request.id}, status={execution_request.status}") # Log ExecutionRequest save
            else: # Handle serializer validation errors
                logger.warning(f"ExecutionRequestAPIView: Invalid execution request data from user '{request.user.username}': {serializer.errors}")
                logger.debug("ExecutionRequestAPIView: post - END - Error Response - ExecutionRequestSerializer validation failed") # Log end of error flow
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
            logger.debug("ExecutionRequestAPIView: Executing with Piston") # Log sandbox type
            compile_output, compile_error, run_output, run_error = execute_piston(execution_request) # Standard execution
            if compile_output is None and compile_error is None and run_output is None and run_error is None:
                execution_success = False
                error_message = "Failed to execute code with Piston API (standard execution)."
            else:
                run_output = run_output

        elif sandbox_type == 'custom':
            logger.debug("ExecutionRequestAPIView: Executing with Custom Sandbox") # Log sandbox type
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
            logger.debug(f"ExecutionRequestAPIView: Retrieved test cases for exercise '{current_exercise.title}': {test_cases}")


            if test_cases: # Only execute test cases if they exist
                logger.debug(f"ExecutionRequestAPIView: Starting test case execution loop for request ID '{execution_request.id}'.")
                for test_case in test_cases:
                    test_input = test_case.get("input", "")
                    expected_output = test_case.get("expected_output", "")
                    logger.debug(f"ExecutionRequestAPIView: Executing test case: Input='{test_input}', Expected Output='{expected_output}'")

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
                    logger.debug(f"ExecutionRequestAPIView: Test case result: {test_case_result}")

                logger.debug(f"ExecutionRequestAPIView: Test case execution loop completed for request ID '{execution_request.id}'. Total test cases: {len(test_case_results)}")


        if execution_success: # Process result only if execution was successful in calling API
            logger.debug("ExecutionRequestAPIView: Execution successful, creating ExecutionResult") # Log before create_execution_result
            execution_result = create_execution_result(
                execution_request,
                compile_output,
                compile_error,
                run_output,
                run_error,
                test_results=test_case_results if test_cases else None # Pass test_results conditionally
            )
            logger.debug(f"ExecutionRequestAPIView: ExecutionResult created with id={execution_result.id}") # Log after create_execution_result

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

            logger.debug("ExecutionRequestAPIView: Before execution_request.save() (status update)") # Log before status update save
            execution_request.save()
            logger.debug(f"ExecutionRequestAPIView: ExecutionRequest status updated to {execution_request.status}") # Log status update save
            result_serializer = ExecutionResultSerializer(execution_result)
            logger.debug("ExecutionRequestAPIView: post - END - Success Response") # Log end of success flow
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)

        else: # Handle overall execution failures
            execution_request.status = 'failed'
            logger.debug("ExecutionRequestAPIView: Execution failed, setting status to failed") # Log execution failure status
            logger.debug("ExecutionRequestAPIView: Before execution_request.save() (failure status)") # Log before failure status save
            execution_request.save()
            logger.debug(f"ExecutionRequestAPIView: ExecutionRequest status updated to {execution_request.status} (failure)") # Log failure status save
            execution_result = ExecutionResult.objects.create(
                request=execution_request,
                output="Execution failed.",
                error=error_message
            )
            result_serializer = ExecutionResultSerializer(execution_result)
            logger.error(f"Execution request ID '{execution_request.id}' failed: {error_message}")
            logger.debug("ExecutionRequestAPIView: post - END - Error Response - Overall execution failure") # Log end of error flow
            return Response(result_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.debug("ExecutionRequestAPIView: post - END - Fallback Response (should not be reached)") # Log end - fallback (should not be reached)



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
