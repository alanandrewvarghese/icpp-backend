import requests
import json
import logging
from .models import ExecutionResult  # Import ExecutionResult model

logger = logging.getLogger("sandbox") # Get logger for sandbox app
def create_execution_result(request, compile_output, compile_error, run_output, run_error, test_results=None):
    """
    ...
    Returns:
        ExecutionResult: The created and saved ExecutionResult instance. # ADDED in description
    """
    output = run_output # Format run output
    error = compile_error or run_error  # Determine error message (compile or run error)
    execution_result = ExecutionResult.objects.create( # Capture the created object
        request=request,
        output=output,
        error=error,
        test_results=test_results
    )
    return execution_result # Return the created object # ADDED line

def execute_code_in_sandbox(api_url, payload):
    """
    Generic utility function to execute code in a sandbox via an API call.

    Args:
        api_url (str): The URL of the sandbox API endpoint.
        payload (dict): The JSON payload to send to the API.

    Returns:
        dict: The JSON response from the API on success, None on failure.
    """
    headers = {'Content-Type': 'application/json'}
    try:
        logger.debug(f"Sending request to sandbox API: {api_url}. Payload: {payload}")
        response = requests.post(api_url, json=payload, headers=headers) # Send payload as JSON
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json() # Parse JSON response
    except requests.exceptions.RequestException as e:
        logger.error(f"Error communicating with sandbox API at {api_url}: {e}. Response content: {e.response.content if e.response else 'No response content'}")
        return None # Indicate failure


def execute_piston(execution_request, test_input=None):
    """
    Executes code using the Piston API.

    Args:
        execution_request (ExecutionRequest): The execution request object.
        test_input (str, optional): Input to provide to the code as stdin. Defaults to None.

    Returns:
        tuple: (compile_output, compile_error, run_output, run_error) or (None, None, None, None) on failure.
    """
    piston_api_url = "http://localhost:2000/api/v2/execute"  # Piston API endpoint
    stdin = test_input or execution_request.stdin or '' # Use empty string if stdin is None
    args_str = execution_request.args or '' # Use empty string if args is None
    args_list = [arg.strip() for arg in args_str.split(',') if arg.strip()]  # Split comma-separated args to list

    piston_payload = {
        "language": "python",
        "version": "3.10.0",
        "files": [
            {
                "name": "main.py",
                "content": execution_request.code
            }
        ],
        "stdin": stdin,
        "args": args_list,
        "compile_timeout": 10000,
        "run_timeout": 3000,
        "compile_memory_limit": -1,
        "run_memory_limit": -1
    }

    if test_input is not None:
        piston_payload["stdin"] = test_input # Override stdin if test_input is provided

    piston_data = execute_code_in_sandbox(piston_api_url, piston_payload)
    if piston_data: # Check if we got a valid response
        compile_output = piston_data.get("compile", {}).get("output", "")  # Get compile output, default to empty string
        compile_error = piston_data.get("compile", {}).get("stderr", "")  # Get compile error, default to empty string
        run_output = piston_data.get("run", {}).get("stdout", "")  # Get run output
        run_error = piston_data.get("run", {}).get("stderr", "")  # Get run error
        return compile_output, compile_error, run_output, run_error
    return None, None, None, None # Indicate failure


def execute_custom_sandbox(execution_request, test_input=None):
    """
    Executes code using the Custom Sandbox API.

    Args:
        execution_request (ExecutionRequest): The execution request object.
        test_input (str, optional): Input to provide to the code as stdin. Defaults to None.

    Returns:
        tuple: (compile_output, compile_error, run_output, run_error) or (None, None, None, None) on failure.
                For custom sandbox, compile_output and compile_error will be empty strings.
    """
    custom_sandbox_api_url = "http://localhost:2001/execute"
    custom_sandbox_payload = {
        "code": execution_request.code,
        #"stdin": "" # Assume custom sandbox API also takes "stdin" - adjust if needed
    }
    if test_input is not None:
        custom_sandbox_payload["stdin"] = test_input # Set stdin to test_input for test case execution


    custom_sandbox_data = execute_code_in_sandbox(custom_sandbox_api_url, custom_sandbox_payload)
    if custom_sandbox_data: # Check for valid response
        run_output = custom_sandbox_data.get("output", "") # Get run output
        run_error = custom_sandbox_data.get("errors", "") # Get run error
        return "", "", run_output, run_error # Compile output/error is not relevant for custom sandbox
    return None, None, None, None # Indicate failure