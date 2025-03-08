from django.urls import path
from .api_views import ExecutionRequestAPIView, ExecutionResultAPIView

urlpatterns = [
    path('execution-requests/', ExecutionRequestAPIView.as_view(), name='create-execution-request'), # POST to create a new execution request
    path('execution-results/<int:request_id>/', ExecutionResultAPIView.as_view(), name='get-execution-result'), # GET to retrieve execution result by request ID
]