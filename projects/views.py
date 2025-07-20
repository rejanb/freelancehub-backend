# projects/views.py
from rest_framework import viewsets, permissions, filters
from .models import Project, Category
from .serializers import ProjectSerializer, CategorySerializer
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.client == request.user

class ProjectPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'status', 'location']
    ordering_fields = ['created_at', 'deadline', 'budget']
    pagination_class = ProjectPagination

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Project.objects.none()
        if user.is_superuser:
            return Project.objects.all().select_related('client', 'selected_freelancer', 'category')
        if user.user_type == 'client':
            return Project.objects.filter(client=user).select_related('client', 'selected_freelancer', 'category')
        if user.user_type == 'freelancer':
            return Project.objects.filter(selected_freelancer=user).select_related('client', 'selected_freelancer', 'category')
        return Project.objects.none()

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

class CategoryPagination(PageNumberPagination):
    page_size = 10000
    page_size_query_param = 'page_size'
    max_page_size = 10000

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CategoryPagination
