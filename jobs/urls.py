from django.urls import path, include
from rest_framework.routers import DefaultRouter

from jobs.views import JobViewSet

router = DefaultRouter()
router.register(r'', JobViewSet, basename='job')  # register without 'jobs/'

urlpatterns = [
    path('', include(router.urls)),
]