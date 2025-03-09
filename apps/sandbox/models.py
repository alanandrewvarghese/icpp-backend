from django.db import models
from django.conf import settings
User = settings.AUTH_USER_MODEL

class ExecutionRequest(models.Model):
    """Stores a request to execute code in a sandbox."""
    user = models.ForeignKey(User, on_delete=models.CASCADE) # Links the request to a user from the accounts app
    exercise = models.ForeignKey("lessons.Exercise", on_delete=models.CASCADE, null=True, blank=True) # Optionally link to an exercise from the lessons app
    code = models.TextField() # Stores the code to be executed
    stdin = models.TextField(blank=True, null=True) # Store stdin in the model
    args = models.TextField(blank=True, null=True) # Stores command-line arguments
    sandbox = models.CharField(max_length=50, default="piston") # Specifies the sandbox to use (e.g., piston, custom)
    created_at = models.DateTimeField(auto_now_add=True) # Timestamp when the request was created
    status = models.CharField(max_length=20, choices=[ # Status of the execution request
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending')

    def __str__(self):
        return f"Execution by {self.user.username} on {self.created_at}"

class ExecutionResult(models.Model):
    """Stores the result of an execution request."""
    request = models.OneToOneField(ExecutionRequest, on_delete=models.CASCADE) # One-to-one link to the execution request
    output = models.TextField(blank=True, null=True) # Stores the standard output of the code execution
    error = models.TextField(blank=True, null=True) # Stores any errors during execution
    execution_time = models.FloatField(null=True, blank=True) # Stores the execution time, if available
    test_results = models.JSONField(default=list, blank=True, null=True) # Format: {"test_case": {"input": "input1", "expected_output": "output1"}, "actual_output": "actual output from the code", "passed": true/false}

    def __str__(self):
        return f"Result for {self.request.id} - {self.request.status}"