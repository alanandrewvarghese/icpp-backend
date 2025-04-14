# Generated by Django 5.1.6 on 2025-04-14 07:27

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CompletionStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(choices=[('lesson', 'Lesson'), ('quiz', 'Quiz'), ('exercise', 'Exercise')], max_length=20)),
                ('content_id', models.PositiveIntegerField()),
                ('completed', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='completion_statuses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['user', 'content_type'], name='status_comp_user_id_1b705b_idx'), models.Index(fields=['content_type', 'content_id'], name='status_comp_content_ecbd88_idx')],
                'unique_together': {('user', 'content_type', 'content_id')},
            },
        ),
    ]
