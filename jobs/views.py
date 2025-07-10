from rest_framework import viewsets, permissions
from .models import Job
from .serializers import JobSerializer
from rest_framework.permissions import AllowAny


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.AllowAny]  # or IsAuthenticated

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

# class JobListCreateView(generics.ListCreateAPIView):
#     queryset = Job.objects.all()
#     serializer_class = JobSerializer
#     permission_classes = [AllowAny]
#
#     def perform_create(self, serializer):
#         serializer.save(client=self.request.user)
#
# class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Job.objects.all()
#     serializer_class = JobSerializer
#     permission_classes = [AllowAny]
