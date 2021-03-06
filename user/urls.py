from django.urls import include, path
from rest_framework import routers

from user import views

router = routers.SimpleRouter()
router.register(r"users", views.UserViewSet)
router.register(r"groups", views.GroupViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
