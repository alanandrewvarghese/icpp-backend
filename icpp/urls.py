from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/lessons/', include('apps.lessons.urls')),
    path('api/sandbox/', include('apps.sandbox.urls')),
    path('api/progress/', include('apps.progress.urls')),
    path('api/badges/', include('apps.badges.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/support/', include('apps.support.urls')),
    path('api/quiz/', include('apps.quiz.urls')),
    path('api/status/', include('apps.status.urls')),
]
