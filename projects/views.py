# projects/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Project, Category, ProjectProposal, ProjectAttachment, SavedProject
from .serializers import (ProjectSerializer, CategorySerializer, ProjectProposalSerializer, 
                         ProjectAttachmentSerializer, SavedProjectSerializer)

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
            return Project.objects.filter(is_public=True).select_related('client', 'selected_freelancer', 'category')
        if user.is_superuser:
            return Project.objects.all().select_related('client', 'selected_freelancer', 'category')
        if user.user_type == 'client':
            return Project.objects.filter(client=user).select_related('client', 'selected_freelancer', 'category')
        if user.user_type == 'freelancer':
            return Project.objects.filter(
                Q(selected_freelancer=user) | Q(is_public=True)
            ).select_related('client', 'selected_freelancer', 'category')
        return Project.objects.filter(is_public=True).select_related('client', 'selected_freelancer', 'category')

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_projects(self, request):
        """Get projects specific to current user"""
        user = request.user
        if user.user_type == 'client':
            queryset = Project.objects.filter(client=user)
        elif user.user_type == 'freelancer':
            queryset = Project.objects.filter(selected_freelancer=user)
        else:
            queryset = Project.objects.none()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def available_projects(self, request):
        """Get available projects for freelancers (open projects without assigned freelancer)"""
        if request.user.user_type != 'freelancer':
            return Response({'detail': 'Only freelancers can access this endpoint.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        queryset = Project.objects.filter(
            status='open', 
            selected_freelancer__isnull=True,
            is_public=True
        ).select_related('client', 'category')
        
        # Apply filters
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        budget_min = request.query_params.get('budget_min')
        if budget_min:
            queryset = queryset.filter(budget__gte=budget_min)
        
        budget_max = request.query_params.get('budget_max')
        if budget_max:
            queryset = queryset.filter(budget__lte=budget_max)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured_projects(self, request):
        """Get featured projects (public to all users)"""
        queryset = Project.objects.filter(is_featured=True, is_public=True).select_related('client', 'category')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def admin_overview(self, request):
        """Get admin overview with statistics (admin only)"""
        if not request.user.is_superuser:
            return Response({'detail': 'Admin access required.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        from django.db.models import Count, Avg
        
        stats = {
            'total_projects': Project.objects.count(),
            'open_projects': Project.objects.filter(status='open').count(),
            'in_progress_projects': Project.objects.filter(status='in_progress').count(),
            'completed_projects': Project.objects.filter(status='completed').count(),
            'total_proposals': ProjectProposal.objects.count(),
            'pending_proposals': ProjectProposal.objects.filter(status='pending').count(),
            'accepted_proposals': ProjectProposal.objects.filter(status='accepted').count(),
            'average_budget': Project.objects.aggregate(avg_budget=Avg('budget'))['avg_budget'],
            'projects_by_category': list(
                Project.objects.values('category__name')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
        }
        
        return Response(stats)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def assign_freelancer(self, request, pk=None):
        """Assign a freelancer to a project (client only)"""
        project = self.get_object()
        
        if project.client != request.user and not request.user.is_superuser:
            return Response({'detail': 'Only the project owner can assign freelancers.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        freelancer_id = request.data.get('freelancer_id')
        if not freelancer_id:
            return Response({'detail': 'freelancer_id is required.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from users.models import CustomUser
            freelancer = CustomUser.objects.get(id=freelancer_id, user_type='freelancer')
            project.selected_freelancer = freelancer
            project.status = 'in_progress'
            project.save()
            
            # Accept the freelancer's proposal if exists
            proposal = ProjectProposal.objects.filter(
                project=project, freelancer=freelancer
            ).first()
            if proposal:
                proposal.status = 'accepted'
                proposal.save()
            
            # Reject other proposals
            ProjectProposal.objects.filter(
                project=project, status='pending'
            ).exclude(freelancer=freelancer).update(status='rejected')
            
            serializer = self.get_serializer(project)
            return Response(serializer.data)
            
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Freelancer not found.'}, 
                          status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_completed(self, request, pk=None):
        """Mark project as completed (client only)"""
        project = self.get_object()
        
        if project.client != request.user and not request.user.is_superuser:
            return Response({'detail': 'Only the project owner can mark projects as completed.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        project.status = 'completed'
        project.completed_at = timezone.now()
        project.save()
        
        serializer = self.get_serializer(project)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def apply(self, request, pk=None):
        """Apply for a project (freelancers only)"""
        project = self.get_object()
        
        if request.user.user_type != 'freelancer':
            return Response({'detail': 'Only freelancers can apply for projects.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if project.status != 'open':
            return Response({'detail': 'This project is not open for applications.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Check if already applied
        existing_proposal = ProjectProposal.objects.filter(
            project=project, freelancer=request.user
        ).first()
        
        if existing_proposal:
            return Response({'detail': 'You have already applied for this project.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ProjectProposalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project=project, freelancer=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def proposals(self, request, pk=None):
        """Get all proposals for a specific project (client and admin only)"""
        project = self.get_object()
        
        if project.client != request.user and not request.user.is_superuser:
            return Response({'detail': 'Only the project owner can view proposals.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        proposals = ProjectProposal.objects.filter(project=project).select_related('freelancer')
        serializer = ProjectProposalSerializer(proposals, many=True)
        return Response({'results': serializer.data})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_applications(self, request):
        """Get freelancer's project applications"""
        if request.user.user_type != 'freelancer':
            return Response({'detail': 'Only freelancers can access this endpoint.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        proposals = ProjectProposal.objects.filter(
            freelancer=request.user
        ).select_related('project')
        
        page = self.paginate_queryset(proposals)
        if page is not None:
            serializer = ProjectProposalSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProjectProposalSerializer(proposals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def save_project(self, request, pk=None):
        """Save/bookmark a project"""
        project = self.get_object()
        saved_project, created = SavedProject.objects.get_or_create(
            user=request.user, project=project
        )
        
        if created:
            return Response({'message': 'Project saved successfully.'})
        else:
            return Response({'message': 'Project already saved.'})

    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def unsave_project(self, request, pk=None):
        """Unsave/unbookmark a project"""
        project = self.get_object()
        saved_project = SavedProject.objects.filter(
            user=request.user, project=project
        ).first()
        
        if saved_project:
            saved_project.delete()
            return Response({'message': 'Project unsaved successfully.'})
        else:
            return Response({'message': 'Project was not saved.'}, 
                          status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def saved_projects(self, request):
        """Get user's saved projects"""
        saved_projects = SavedProject.objects.filter(
            user=request.user
        ).select_related('project').order_by('-saved_at')
        
        page = self.paginate_queryset(saved_projects)
        if page is not None:
            serializer = SavedProjectSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = SavedProjectSerializer(saved_projects, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def is_saved(self, request, pk=None):
        """Check if a project is saved by current user"""
        project = self.get_object()
        is_saved = SavedProject.objects.filter(
            user=request.user, project=project
        ).exists()
        return Response({'is_saved': is_saved})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upload_attachment(self, request, pk=None):
        """Upload an attachment to a project"""
        project = self.get_object()
        
        if project.client != request.user and not request.user.is_superuser:
            return Response({'detail': 'Only the project owner can upload attachments.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'No file provided.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        attachment = ProjectAttachment.objects.create(
            project=project,
            file=file,
            filename=file.name,
            uploaded_by=request.user
        )
        
        serializer = ProjectAttachmentSerializer(attachment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def attachments(self, request, pk=None):
        """Get attachments for a project"""
        project = self.get_object()
        attachments = ProjectAttachment.objects.filter(project=project)
        serializer = ProjectAttachmentSerializer(attachments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def contract_files(self, request, pk=None):
        """Get contract files for a project"""
        project = self.get_object()
        
        # Check if user has access to this project
        if (project.client != request.user and 
            project.selected_freelancer != request.user and 
            not request.user.is_superuser):
            return Response({'detail': 'You do not have access to this project.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Get contract if exists
        try:
            from contracts.models import Contract, ContractDocument
            contract = Contract.objects.get(project_proposal__project=project)
            documents = ContractDocument.objects.filter(contract=contract)
            
            from contracts.serializers import ContractDocumentSerializer
            serializer = ContractDocumentSerializer(documents, many=True)
            return Response(serializer.data)
        except Contract.DoesNotExist:
            return Response([])  # No contract yet, return empty list

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upload_contract_file(self, request, pk=None):
        """Upload a contract file to a project"""
        project = self.get_object()
        
        # Check if user has access to this project
        if (project.client != request.user and 
            project.selected_freelancer != request.user and 
            not request.user.is_superuser):
            return Response({'detail': 'You do not have access to this project.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Get or create contract
        try:
            from contracts.models import Contract, ContractDocument
            contract = Contract.objects.get(project_proposal__project=project)
        except Contract.DoesNotExist:
            return Response({'detail': 'No contract exists for this project.'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        file = request.FILES.get('document')
        if not file:
            return Response({'detail': 'No file provided.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        document = ContractDocument.objects.create(
            contract=contract,
            file=file,
            filename=file.name,
            uploaded_by=request.user,
            document_type=request.data.get('document_type', 'contract')
        )
        
        from contracts.serializers import ContractDocumentSerializer
        serializer = ContractDocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def delete_contract_file(self, request, pk=None, file_id=None):
        """Delete a contract file"""
        project = self.get_object()
        
        # Check if user has access to this project
        if (project.client != request.user and 
            project.selected_freelancer != request.user and 
            not request.user.is_superuser):
            return Response({'detail': 'You do not have access to this project.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        file_id = request.data.get('file_id') or file_id
        if not file_id:
            return Response({'detail': 'file_id is required.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from contracts.models import ContractDocument
            document = ContractDocument.objects.get(
                id=file_id,
                contract__project_proposal__project=project
            )
            document.delete()
            return Response({'message': 'File deleted successfully.'})
        except ContractDocument.DoesNotExist:
            return Response({'detail': 'File not found.'}, 
                          status=status.HTTP_404_NOT_FOUND)


class CategoryPagination(PageNumberPagination):
    page_size = 10000
    page_size_query_param = 'page_size'
    max_page_size = 10000

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CategoryPagination


class ProposalViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectProposalSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ProjectPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ProjectProposal.objects.all().select_related('project', 'freelancer')
        elif user.user_type == 'client':
            return ProjectProposal.objects.filter(
                project__client=user
            ).select_related('project', 'freelancer')
        elif user.user_type == 'freelancer':
            return ProjectProposal.objects.filter(
                freelancer=user
            ).select_related('project', 'freelancer')
        return ProjectProposal.objects.none()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def accept(self, request, pk=None):
        """Accept a proposal (client and admin only)"""
        proposal = self.get_object()
        
        if (proposal.project.client != request.user and not request.user.is_superuser):
            return Response({'detail': 'Only the project owner can accept proposals.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if proposal.status != 'pending':
            return Response({'detail': 'Proposal is not in pending status.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Accept this proposal
        proposal.status = 'accepted'
        proposal.save()
        
        # Assign freelancer to project
        project = proposal.project
        project.selected_freelancer = proposal.freelancer
        project.status = 'in_progress'
        project.save()
        
        # Reject other pending proposals
        ProjectProposal.objects.filter(
            project=project, status='pending'
        ).exclude(id=proposal.id).update(status='rejected')
        
        serializer = self.get_serializer(proposal)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        """Reject a proposal (client and admin only)"""
        proposal = self.get_object()
        
        if (proposal.project.client != request.user and not request.user.is_superuser):
            return Response({'detail': 'Only the project owner can reject proposals.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if proposal.status != 'pending':
            return Response({'detail': 'Proposal is not in pending status.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        proposal.status = 'rejected'
        proposal.save()
        
        serializer = self.get_serializer(proposal)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def withdraw(self, request, pk=None):
        """Withdraw a proposal (freelancer only)"""
        proposal = self.get_object()
        
        if proposal.freelancer != request.user and not request.user.is_superuser:
            return Response({'detail': 'You can only withdraw your own proposals.'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if proposal.status != 'pending':
            return Response({'detail': 'Proposal is not in pending status.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        proposal.status = 'withdrawn'
        proposal.save()
        
        serializer = self.get_serializer(proposal)
        return Response(serializer.data)
