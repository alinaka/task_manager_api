from rest_framework import viewsets

from core.models import Task
from core.serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Task.objects.all().order_by("due_date")
    serializer_class = TaskSerializer
