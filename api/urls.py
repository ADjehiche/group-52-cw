"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.http import HttpResponse
from . import views
from .views import main_spa

urlpatterns = [
    path("api/items/", views.items_collection, name="items_collection"),
    path("api/logout/", views.api_logout, name="api_logout"),
    path("api/auth/status/", views.auth_status, name="auth_status"),
    path("api/profile/", views.profile_api, name="profile_api"),
    path("", views.main_spa, name="main_spa"),
]
