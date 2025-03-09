import requests
import logging
from django.conf import settings

logger = logging.getLogger("progress")

def send_execution_request(execution_request_data, token=None):
    """
    Sends a request to the code execution sandbox with the provided data.
    Uses JWT authentication instead of auth_token.
    """
    execution_url = "http://127.0.0.1:8000/api/sandbox/execution-requests/"

    if not execution_url:
        logger.error("Execution service URL is not configured in settings.")
        return {"error": "Execution service URL is missing."}

    headers = {
        "Content-Type": "application/json",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    logger.debug(f"Sending execution request to {execution_url} with data: {execution_request_data} and headers: {headers}")

    try:
        response = requests.post(execution_url, json=execution_request_data, headers=headers)
        
        # Log response details for debugging
        logger.debug(f"Received response: {response.status_code} - {response.text}")

        response.raise_for_status()  # Raises an exception for 4xx and 5xx responses

        return response.json()

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
        return {"error": "HTTP error during execution request.", "details": response.text}
    
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error occurred: {conn_err}")
        return {"error": "Connection to execution service failed."}

    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Request timeout occurred: {timeout_err}")
        return {"error": "Execution request timed out."}

    except Exception as e:
        logger.exception("Unexpected error during execution request.")
        return {"error": "Unexpected error during execution request.", "details": str(e)}
