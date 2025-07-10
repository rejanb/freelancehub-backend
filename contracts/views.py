from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.permissions import AllowAny
from .models import Proposal
from .serializers import ProposalSerializer

class ProposalViewSet(viewsets.ModelViewSet):
    queryset = Proposal.objects.all()
    serializer_class = ProposalSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        serializer.save(freelancer=self.request.user)