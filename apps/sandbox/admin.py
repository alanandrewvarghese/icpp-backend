from django.contrib import admin
from .models import ExecutionRequest, ExecutionResult

# Register your models here.
admin.site.register(ExecutionRequest)
admin.site.register(ExecutionResult)