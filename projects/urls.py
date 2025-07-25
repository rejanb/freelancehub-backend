from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, CategoryViewSet, ProposalViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'categories', CategoryViewSet)

# Proposals are accessed through /api/projects/proposals/ to match frontend
proposal_router = DefaultRouter()
proposal_router.register(r'proposals', ProposalViewSet, basename='proposal')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(proposal_router.urls)),
    # Custom URL for contract file deletion
    path('projects/<int:pk>/contract_files/<int:file_id>/', 
         ProjectViewSet.as_view({'delete': 'delete_contract_file'}), 
         name='project-delete-contract-file'),
    # Public API endpoints (no authentication required)
    path('public/', include('projects.public_urls')),
]