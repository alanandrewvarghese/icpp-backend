from django.test import TestCase
from unittest.mock import patch, Mock
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth import get_user_model
from apps.lessons.models import Exercise, Lesson
from apps.sandbox.api_views import ExecutionRequestAPIView
from apps.sandbox.models import ExecutionRequest, ExecutionResult
import json

User = get_user_model()


class PistonExecutionTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        # Create a Lesson object
        self.lesson = Lesson.objects.create(title="Test Lesson", description="Test lesson description", content="Test lesson content", order=1, created_by=self.user)
        # Associate the Exercise with the Lesson
        self.exercise = Exercise.objects.create(title="Test Exercise", lesson=self.lesson, sandbox="piston", created_by=self.user)
        self.factory = APIRequestFactory()

    @patch('apps.sandbox.utils.requests.post')
    def test_successful_piston_execution(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "language": "python",
            "version": "3.10.0",
            "run": {"stdout": "Hello from Piston!\n", "stderr": "", "code": 0, "signal": None},
            "compile": {}
        }
        mock_post.return_value = mock_response

        request = self.factory.post('/api/sandbox/execution-requests/', {'code': 'print("Hello from Piston!")', 'exercise': self.exercise.id, 'sandbox': 'piston'}, format='json')
        force_authenticate(request, user=self.user)
        view = ExecutionRequestAPIView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ExecutionRequest.objects.count(), 1)
        self.assertEqual(ExecutionResult.objects.count(), 1)
        result = ExecutionResult.objects.first()
        self.assertIn("Run Output:\nHello from Piston!", result.output)
        self.assertEqual(result.error, "")
        self.assertEqual(ExecutionRequest.objects.first().status, 'completed')
        mock_post.assert_called_once()

    @patch('apps.sandbox.utils.requests.post')
    def test_piston_execution_with_stdin(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "language": "python",
            "version": "3.10.0",
            "run": {"stdout": "Program output with input\n", "stderr": "", "code": 0, "signal": None},
            "compile": {}
        }
        mock_post.return_value = mock_response

        stdin_text = "Test input to stdin"

        request = self.factory.post(
            '/api/sandbox/execution-requests/',
            {'code': 'import sys; print(sys.stdin.read())',
             'exercise': self.exercise.id,
             'sandbox': 'piston',
             'stdin': stdin_text},
            format='json'
        )
        force_authenticate(request, user=self.user)
        view = ExecutionRequestAPIView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ExecutionRequest.objects.count(), 1)
        self.assertEqual(ExecutionResult.objects.count(), 1)

        mock_post.assert_called_once()
        # Corrected line: Access payload from 'json' key
        called_payload = mock_post.call_args.kwargs['json']
        self.assertEqual(called_payload['stdin'], stdin_text)

    @patch('apps.sandbox.utils.requests.post')
    def test_piston_execution_with_args(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "language": "python",
            "version": "3.10.0",
            "run": {"stdout": "Arguments: arg1 arg2 arg3\n", "stderr": "", "code": 0, "signal": None},
            "compile": {}
        }
        mock_post.return_value = mock_response

        args_text = "arg1, arg2, arg3"

        request = self.factory.post(
            '/api/sandbox/execution-requests/',
            {'code': 'import sys; print("Arguments:", *sys.argv[1:])',
             'exercise': self.exercise.id,
             'sandbox': 'piston',
             'args': args_text},
            format='json'
        )
        force_authenticate(request, user=self.user)
        view = ExecutionRequestAPIView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ExecutionRequest.objects.count(), 1)
        self.assertEqual(ExecutionResult.objects.count(), 1)

        mock_post.assert_called_once()
        # Corrected line: Access payload from 'json' key
        called_payload = mock_post.call_args.kwargs['json']
        self.assertEqual(called_payload['args'], ["arg1", "arg2", "arg3"])

    @patch('apps.sandbox.utils.requests.post')
    def test_piston_execution_compile_error(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200  # Still a successful HTTP response (from API perspective)
        mock_response.json.return_value = {
            "language": "python",
            "version": "3.10.0",
            "compile": {
                "stdout": "",
                "stderr": "SyntaxError: invalid syntax (main.py, line 1)\n", # Simulate a Python syntax error
                "code": 1, # Non-zero compile code (optional, but good practice)
                "signal": None,
                "output": "SyntaxError: invalid syntax (main.py, line 1)\n" # Combined output (optional)
            },
            "run": { # Run section should be empty or have default values in case of compile error
                "stdout": "",
                "stderr": "",
                "code": 0,
                "signal": None,
                "output": ""
            }
        }
        mock_post.return_value = mock_response

        invalid_code = "def invalid python code here" # Code with syntax error

        request = self.factory.post(
            '/api/sandbox/execution-requests/',
            {'code': invalid_code,
             'exercise': self.exercise.id,
             'sandbox': 'piston'},
            format='json'
        )
        force_authenticate(request, user=self.user)
        view = ExecutionRequestAPIView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ExecutionRequest.objects.count(), 1)
        self.assertEqual(ExecutionResult.objects.count(), 1)

        result = ExecutionResult.objects.first()
        self.assertIn("Run Output:", result.output)  # Check for "Run Output" in output
        self.assertIn("SyntaxError: invalid syntax", result.error)  # Crucial Assertion: Check for the specific syntax error message in error
        self.assertEqual(ExecutionRequest.objects.first().status, 'failed')  # Check that execution status is set to 'failed'


class PistonExecutionWithTestsTests(TestCase):

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='testuser_test', password='testpassword')
        self.lesson = Lesson.objects.create(title="Test Lesson", description="Test lesson description", content="Test lesson content", order=1, created_by=self.user)
        self.exercise = Exercise.objects.create(
            title="Test Exercise with Tests",
            lesson=self.lesson,
            sandbox="piston",
            created_by=self.user,
            structured_test_cases=[
                {"input": "2 3", "expected_output": "5"},
                {"input": "10 5", "expected_output": "15"},
            ]
        )
        self.factory = APIRequestFactory()

    @patch('apps.sandbox.utils.requests.post')
    def test_piston_execution_with_test_cases_success(self, mock_post):
        # Mock Piston API to return successful output for all test cases
        def side_effect(url, *args, **kwargs): # Define a side effect function
            mock_response = Mock()
            mock_response.status_code = 200
            payload = kwargs.get('json') # Get payload from json argument
            input_val = payload.get('stdin', '')
            if input_val == "2 3":
                mock_response.json.return_value = {"run": {"stdout": "5\n", "stderr": "", "code": 0, "signal": None}, "compile": {}}
            elif input_val == "10 5":
                mock_response.json.return_value = {"run": {"stdout": "15\n", "stderr": "", "code": 0, "signal": None}, "compile": {}}
            else: # Default case, adjust as needed
                mock_response.json.return_value = {"run": {"stdout": "Default Output\n", "stderr": "", "code": 0, "signal": None}, "compile": {}}
            return mock_response
        mock_post.side_effect = side_effect # Set the side effect

        request_data = {'code': 'input_vals = input().split(); print(int(input_vals[0]) + int(input_vals[1]))', 'exercise': self.exercise.id, 'sandbox': 'piston'}
        request = self.factory.post('/api/sandbox/execution-requests/', request_data, format='json')
        force_authenticate(request, user=self.user)
        view = ExecutionRequestAPIView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 201)
        result = ExecutionResult.objects.first()
        self.assertIsNotNone(result.test_results)
        self.assertEqual(len(result.test_results), 2) # Check number of test cases
        for test_result in result.test_results:
            self.assertTrue(test_result['passed']) # Assert all tests passed

    @patch('apps.sandbox.utils.requests.post')
    def test_piston_execution_with_test_cases_failure(self, mock_post):
        # Mock Piston API to return successful output for first test case and failure for second
        def side_effect(url, *args, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            payload = kwargs.get('json') # Get payload from json argument
            input_val = payload.get('stdin', '')
            if input_val == "2 3":
                mock_response.json.return_value = {"run": {"stdout": "5\n", "stderr": "", "code": 0, "signal": None}, "compile": {}}
            elif input_val == "10 5":
                mock_response.json.return_value = {"run": {"stdout": "10\n", "stderr": "", "code": 0, "signal": None}, "compile": {}} # Incorrect output for failure
            else:
                mock_response.json.return_value = {"run": {"stdout": "Default Output\n", "stderr": "", "code": 0, "signal": None}, "compile": {}}
            return mock_response
        mock_post.side_effect = side_effect

        request_data = {'code': 'input_vals = input().split(); print(int(input_vals[0]) + int(input_vals[1]))', 'exercise': self.exercise.id, 'sandbox': 'piston'}
        request = self.factory.post('/api/sandbox/execution-requests/', request_data, format='json')
        force_authenticate(request, user=self.user)
        view = ExecutionRequestAPIView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 201)
        result = ExecutionResult.objects.first()
        self.assertIsNotNone(result.test_results)
        self.assertEqual(len(result.test_results), 2)
        passed_count = 0
        failed_count = 0
        for test_result in result.test_results:
            if test_result['passed']:
                passed_count += 1
            else:
                failed_count += 1
        self.assertEqual(passed_count, 1) # One test case should pass
        self.assertEqual(failed_count, 1) # One test case should fail