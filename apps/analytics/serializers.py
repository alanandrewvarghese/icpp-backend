from rest_framework import serializers

class LessonStatsSerializer(serializers.Serializer):
    """Serializer for overall lesson analytics stats"""
    total_lessons = serializers.IntegerField()
    total_students = serializers.IntegerField()
    total_completions = serializers.IntegerField()
    overall_completion_percentage = serializers.FloatField()


class LessonDetailSerializer(serializers.Serializer):
    """Serializer for individual lesson analytics data"""
    id = serializers.IntegerField()
    title = serializers.CharField()
    completion_count = serializers.IntegerField()
    completion_rate = serializers.FloatField()


class LessonTrendSerializer(serializers.Serializer):
    """Serializer for lesson completion trend data"""
    day = serializers.DateTimeField()
    count = serializers.IntegerField()


class LessonAnalyticsSerializer(serializers.Serializer):
    """Main serializer for lesson analytics endpoint"""
    overall_stats = LessonStatsSerializer()
    top_completed_lessons = LessonDetailSerializer(many=True)
    lowest_completion_lessons = LessonDetailSerializer(many=True)
    completion_trend = LessonTrendSerializer(many=True)


class ExerciseStatsSerializer(serializers.Serializer):
    """Serializer for overall exercise analytics stats"""
    total_submissions = serializers.IntegerField()
    correct_submissions = serializers.IntegerField()
    incorrect_submissions = serializers.IntegerField()
    success_rate = serializers.FloatField()


class ExerciseDetailSerializer(serializers.Serializer):
    """Serializer for individual exercise analytics data"""
    id = serializers.IntegerField()
    title = serializers.CharField()
    total_attempts = serializers.IntegerField()
    correct_attempts = serializers.IntegerField()
    success_rate = serializers.FloatField()


class ExerciseTrendSerializer(serializers.Serializer):
    """Serializer for exercise submission trend data"""
    day = serializers.DateTimeField()
    total = serializers.IntegerField()
    correct = serializers.IntegerField()
    incorrect = serializers.IntegerField()


class ErrorTypeSerializer(serializers.Serializer):
    """Serializer for error type distribution data"""
    error_type = serializers.CharField(allow_null=True)
    count = serializers.IntegerField()


class ExerciseAnalyticsSerializer(serializers.Serializer):
    """Main serializer for exercise analytics endpoint"""
    overall_stats = ExerciseStatsSerializer()
    most_attempted_exercises = ExerciseDetailSerializer(many=True)
    challenging_exercises = ExerciseDetailSerializer(many=True)
    submission_trend = ExerciseTrendSerializer(many=True)
    common_error_types = ErrorTypeSerializer(many=True)


class SandboxStatsSerializer(serializers.Serializer):
    """Serializer for overall sandbox analytics stats"""
    total_executions = serializers.IntegerField()
    successful_executions = serializers.IntegerField()
    failed_executions = serializers.IntegerField()
    success_rate = serializers.FloatField()
    avg_execution_time_seconds = serializers.FloatField(allow_null=True)


class SandboxTrendSerializer(serializers.Serializer):
    """Serializer for execution trend data"""
    day = serializers.DateTimeField()
    total = serializers.IntegerField()
    successful = serializers.IntegerField()
    failed = serializers.IntegerField()


class LanguageDistributionSerializer(serializers.Serializer):
    """Serializer for language distribution data"""
    language = serializers.CharField()
    count = serializers.IntegerField()


class SandboxAnalyticsSerializer(serializers.Serializer):
    """Main serializer for sandbox analytics endpoint"""
    overall_stats = SandboxStatsSerializer()
    execution_trend = SandboxTrendSerializer(many=True)
    common_error_types = ErrorTypeSerializer(many=True)
    language_distribution = LanguageDistributionSerializer(many=True)
