from django.urls import path
from .views import DisputeListCreateView, DisputeDetailView, DisputeResolveView

urlpatterns = [
    path('', DisputeListCreateView.as_view(), name='dispute-list-create'),
    path('<int:pk>/', DisputeDetailView.as_view(), name='dispute-detail'),
    path('<int:pk>/resolve/', DisputeResolveView.as_view(), name='dispute-resolve'),
]

