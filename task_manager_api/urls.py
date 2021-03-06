"""task_manager_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path("", views.home, name="home")
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path("", Home.as_view(), name="home")
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path("blog/", include("blog.urls"))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from core.urls import urlpatterns as core_urls
from task_manager_api import views
from user.urls import urlpatterns as user_urls

api_urls = [
    path("", include(user_urls)),
    path("", include(core_urls))
]

urlpatterns = [
    path("", views.APIRootView.as_view()),
    path("api/", include(api_urls)),
    path("login/", obtain_auth_token)
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
