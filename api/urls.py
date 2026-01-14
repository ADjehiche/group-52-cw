from django.urls import path

from .views import items_collection, main_spa

urlpatterns = [
    path("api/items/", items_collection, name="api-items-collection"),
    path("items/", items_collection, name="items-collection"),  # legacy /items/ for dev proxy convenience
    path("", main_spa, name="spa"),
]
