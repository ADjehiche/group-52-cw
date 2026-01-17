from django.urls import path

from .views import items_collection, main_spa

urlpatterns = [
    path("api/items/", items_collection, name="api-items-collection"),
    path("", main_spa, name="spa"),
]
