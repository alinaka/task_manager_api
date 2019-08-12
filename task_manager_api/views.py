from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import views


class APIRootView(views.APIView):
    def get(self, request, *args, **kwargs):
        return Response({
            "users": reverse("user-list", request=request),
            "groups": reverse("group-list", request=request),
            "tasks": reverse("task-list", request=request)
        })