from django.urls import path
from .views import DisputeListCreateView, DisputeResolveView

urlpatterns = [
    path('', DisputeListCreateView.as_view(), name='dispute-list-create'),
    path('<int:pk>/resolve/', DisputeResolveView.as_view(), name='dispute-resolve'),
]

