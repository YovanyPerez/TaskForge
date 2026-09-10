from rest_framework import viewsets

from users.permissions import IsAdminOrManagerOrReadOnly, scope_to_member

from .models import Task
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        return scope_to_member(
            super().get_queryset(), self.request.user, project__members=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
