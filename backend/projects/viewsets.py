from rest_framework import viewsets

from users.permissions import IsAdminOrManagerOrReadOnly, scope_to_member

from .models import Project
from .serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        return scope_to_member(
            super().get_queryset(), self.request.user, members=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
