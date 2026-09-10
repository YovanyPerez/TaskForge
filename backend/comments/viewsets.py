from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from tasks.models import Task
from users.permissions import IsOwnerOrManager, scope_to_member

from .models import Comment
from .serializers import CommentSerializer


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOwnerOrManager()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return scope_to_member(
            super().get_queryset(),
            self.request.user,
            task__project__members=self.request.user,
        )

    def perform_create(self, serializer):
        task = serializer.validated_data["task"]
        visible = scope_to_member(
            Task.objects.all(), self.request.user, project__members=self.request.user
        )
        if not visible.filter(pk=task.pk).exists():
            raise PermissionDenied("You must be a member of the project to comment.")
        serializer.save(user=self.request.user)
