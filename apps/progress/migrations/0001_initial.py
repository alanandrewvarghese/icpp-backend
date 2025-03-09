# Generated by Django 5.1.6 on 2025-03-08 06:02

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('lessons', '0003_exercise_sandbox'),
        ('sandbox', '0006_executionresult_test_results'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ExerciseSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submitted_code', models.TextField()),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('is_correct', models.BooleanField(default=False)),
                ('execution_result', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sandbox.executionresult')),
                ('exercise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lessons.exercise')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='LessonProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed_at', models.DateTimeField(auto_now_add=True)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lessons.lesson')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
