from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, NotificationListCreateView, NotificationMarkReadView

# Create router for ViewSet
router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    # ViewSet URLs (recommended) - this will create /api/notifications/ endpoints
    path('', include(router.urls)),
    
    # Legacy URLs for backward compatibility
    path('list/', NotificationListCreateView.as_view(), name='notification-list-create'),
    path('<int:pk>/mark-read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
]

