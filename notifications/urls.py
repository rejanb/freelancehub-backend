from django.urls import path
from .views import NotificationListCreateView, NotificationMarkReadView, NotificationDetailView  

urlpatterns = [
    path('', NotificationListCreateView.as_view(), name='notification-list-create'),
    path('<int:pk>/mark-read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),  
]
