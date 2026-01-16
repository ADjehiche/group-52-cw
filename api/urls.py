from django.urls import path

from .views import item_detail, items_collection, main_spa

urlpatterns = [
    path("api/items/", items_collection, name="api-items-collection"),
    path("api/items/<int:item_id>/", item_detail, name="api-item-detail"),
    path("items/", items_collection, name="items-collection"),  # legacy /items/ for dev proxy convenience
    path("", main_spa, name="spa"),
]
