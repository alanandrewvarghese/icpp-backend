from rest_framework import serializers
from .models import Quiz, Question, Choice, QuizAttempt

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text', 'is_correct']
        extra_kwargs = {
            'is_correct': {'write_only': True}  # Hide correct answers in response
        }

class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'order', 'choices']

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'passing_score', 'questions', 'lesson']

class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'score', 'passed', 'completed_at']
        read_only_fields = ['score', 'passed', 'completed_at']

class QuizSubmissionSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )
