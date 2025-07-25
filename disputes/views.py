from django.shortcuts import render
from rest_framework import generics, permissions, status
from .models import Dispute
from .serializers import DisputeSerializer, CreateDisputeSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import filters

# Create your views here.

class IsFreelancerPermission(permissions.BasePermission):
    """
    Custom permission to only allow freelancers to create and view disputes.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is a freelancer
        return hasattr(request.user, 'freelancer_profile') and request.user.freelancer_profile is not None

class DisputeListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsFreelancerPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        # Only return disputes created by the current user (freelancer)
        queryset = Dispute.objects.filter(created_by=self.request.user).select_related(
            'project', 'contract', 'created_by', 'resolved_by'
        )
        
        # Manual filtering based on query parameters
        priority = self.request.query_params.get('priority')
        dispute_type = self.request.query_params.get('type')
        status_filter = self.request.query_params.get('status')
        project_id = self.request.query_params.get('project')
        contract_id = self.request.query_params.get('contract')
        
        if priority:
            queryset = queryset.filter(priority=priority)
        if dispute_type:
            queryset = queryset.filter(type=dispute_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if project_id:
            queryset = queryset.filter(project__id=project_id)
        if contract_id:
            queryset = queryset.filter(contract__id=contract_id)
            
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateDisputeSerializer
        return DisputeSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        
    def create(self, request, *args, **kwargs):
        # Add additional validation for freelancer-only access
        if not hasattr(request.user, 'freelancer_profile') or not request.user.freelancer_profile:
            return Response(
                {'error': 'Only freelancers can create disputes'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def list(self, request, *args, **kwargs):
        """Enhanced list view with filtering info"""
        base_queryset = Dispute.objects.filter(created_by=self.request.user)
        queryset = self.filter_queryset(self.get_queryset())
        
        # Get filter counts
        filter_counts = {
            'total': base_queryset.count(),
            'filtered_total': queryset.count(),
            'by_priority': {
                priority[0]: base_queryset.filter(priority=priority[0]).count()
                for priority in Dispute.PRIORITY_CHOICES
            },
            'by_type': {
                dispute_type[0]: base_queryset.filter(type=dispute_type[0]).count()
                for dispute_type in Dispute.TYPE_CHOICES
            },
            'by_status': {
                dispute_status[0]: base_queryset.filter(status=dispute_status[0]).count()
                for dispute_status in Dispute.STATUS_CHOICES
            }
        }
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data['filter_counts'] = filter_counts
            response.data['available_filters'] = {
                'priority_choices': Dispute.PRIORITY_CHOICES,
                'type_choices': Dispute.TYPE_CHOICES,
                'status_choices': Dispute.STATUS_CHOICES
            }
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'filter_counts': filter_counts,
            'available_filters': {
                'priority_choices': Dispute.PRIORITY_CHOICES,
                'type_choices': Dispute.TYPE_CHOICES,
                'status_choices': Dispute.STATUS_CHOICES
            }
        })

class DisputeDetailView(generics.RetrieveAPIView):
    serializer_class = DisputeSerializer
    permission_classes = [permissions.IsAuthenticated, IsFreelancerPermission]
    
    def get_queryset(self):
        # Only return disputes created by the current user (freelancer)
        return Dispute.objects.filter(created_by=self.request.user).select_related(
            'project', 'contract', 'created_by', 'resolved_by'
        )

class DisputeResolveView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        try:
            dispute = Dispute.objects.get(pk=pk)
        except Dispute.DoesNotExist:
            return Response({'error': 'Dispute not found'}, status=status.HTTP_404_NOT_FOUND)
        
        resolution = request.data.get('resolution', '')
        status_val = request.data.get('status', 'resolved')
        dispute.resolution = resolution
        dispute.status = status_val
        dispute.resolved_by = request.user
        dispute.save()
        
        return Response({
            'status': 'Dispute resolved', 
            'dispute': DisputeSerializer(dispute).data
        })
