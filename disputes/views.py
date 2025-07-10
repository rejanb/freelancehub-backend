from django.shortcuts import render
from rest_framework import generics, permissions, status
from .models import Dispute
from .serializers import DisputeSerializer
from rest_framework.response import Response
from rest_framework.views import APIView

# Create your views here.

class DisputeListCreateView(generics.ListCreateAPIView):
    queryset = Dispute.objects.all().order_by('-created_at')
    serializer_class = DisputeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

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
        return Response({'status': 'Dispute resolved', 'dispute': DisputeSerializer(dispute).data})
