from django.urls import path

from .views import api_logout, auth_status, item_detail, items_collection, main_spa

urlpatterns = [
    path("api/items/", items_collection, name="api-items-collection"),
    path("api/items/<int:item_id>/", item_detail, name="api-item-detail"),
    path("api/logout/", api_logout, name="api_logout"),
    path("api/auth/status/", auth_status, name="auth_status"),
    path("items/", items_collection, name="items-collection"),  # legacy /items/ for dev proxy convenience
    # Serve SPA for item detail client routes so refreshes don't 404
    path("items/<int:item_id>/", main_spa, name="spa-item-detail"),
    path("", main_spa, name="spa"),
]
