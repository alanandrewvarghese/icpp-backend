import requests
import logging
from django.conf import settings
from rest_framework.test import APIRequestFactory
from apps.sandbox.api_views import ExecutionRequestAPIView

logger = logging.getLogger("progress")

def send_execution_request(execution_request_data, token=None, execution_request_id=None):
    """
    Send an execution request to the sandbox API.

    Args:
        execution_request_data (dict): The data for the execution request
        token (str, optional): JWT token for authentication
        execution_request_id (int, optional): ID of an existing ExecutionRequest object

    Returns:
        Response or dict: The response from the sandbox API
    """
    factory = APIRequestFactory()

    # Create a copy of the execution_request_data to avoid modifying the original
    data_copy = execution_request_data.copy()

    # If an execution_request_id is provided, include it in the data before creating the request
    if execution_request_id:
        data_copy['existing_request_id'] = execution_request_id

    # Create the request with the modified data
    request = factory.post('/api/sandbox/execute/', data_copy)

    if token:
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'

    view = ExecutionRequestAPIView.as_view()
    response = view(request)

    return response.data if hasattr(response, 'data') else response
