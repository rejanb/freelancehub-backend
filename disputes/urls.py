from django.urls import path
from .views import DisputeListCreateView, DisputeResolveView,DisputeDetailView

urlpatterns = [
    path('', DisputeListCreateView.as_view(), name='dispute-list-create'),
    path('<int:pk>/resolve/', DisputeResolveView.as_view(), name='dispute-resolve'),
     path('<int:pk>/', DisputeDetailView.as_view(), name='dispute-detail'), 
]

