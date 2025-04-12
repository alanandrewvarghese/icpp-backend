from rest_framework import serializers
from .models import Quiz, Question, Choice, QuizAttempt
from apps.lessons.models import Lesson

class ChoiceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Choice
        fields = ['id', 'text', 'is_correct', 'question']
        extra_kwargs = {
            'question': {'write_only': True, 'required': False},
        }

class QuestionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'order', 'choices', 'quiz']
        extra_kwargs = {
            'quiz': {'write_only': True, 'required': False},
        }

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    lesson_title = serializers.SerializerMethodField()
    created_by_username = serializers.SerializerMethodField()
    lesson_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'passing_score', 'questions',
                  'lesson', 'lesson_id', 'lesson_title', 'created_at', 'updated_at',
                  'created_by', 'created_by_username']
        extra_kwargs = {
            'created_by': {'write_only': True, 'required': False},
            'lesson': {'required': False},
        }

    def get_lesson_title(self, obj):
        return obj.lesson.title if obj.lesson else None

    def get_created_by_username(self, obj):
        return obj.created_by.username if obj.created_by else None

    def validate(self, data):
        lesson = data.get('lesson')
        lesson_id = data.pop('lesson_id', None)

        # If lesson_id is provided but lesson is not, get the lesson
        if not lesson and lesson_id:
            try:
                lesson = Lesson.objects.get(pk=lesson_id)
                data['lesson'] = lesson
            except Lesson.DoesNotExist:
                raise serializers.ValidationError({"lesson_id": "Lesson not found"})

        # Check that the lesson doesn't already have a quiz
        if lesson and self.instance is None:  # Only for quiz creation
            if Quiz.objects.filter(lesson=lesson).exists():
                raise serializers.ValidationError({"lesson": "This lesson already has a quiz"})

        return data

class QuizAttemptSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    quiz_title = serializers.SerializerMethodField()

    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'quiz_title', 'user', 'username',
                  'score', 'passed', 'completed_at']
        read_only_fields = ['score', 'passed', 'completed_at']

    def get_username(self, obj):
        return obj.user.username

    def get_quiz_title(self, obj):
        return obj.quiz.title

class QuizSubmissionSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )
