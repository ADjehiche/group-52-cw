from django.urls import path

from .views import (
    api_logout,
    auth_status,
    item_detail,
    item_questions_list_or_create,
    items_collection,
    main_spa,
    question_answer,
)

urlpatterns = [
    path("api/items/", items_collection, name="api-items-collection"),
    path("api/items/<int:item_id>/", item_detail, name="api-item-detail"),
    path("api/items/<int:item_id>/questions/", item_questions_list_or_create, name="item_questions"),
    path("api/questions/<int:question_id>/answer/", question_answer, name="question_answer"),
    path("api/logout/", api_logout, name="api_logout"),
    path("api/auth/status/", auth_status, name="auth_status"),
    path("items/", items_collection, name="items-collection"),
    path("items/<int:item_id>/", main_spa, name="spa-item-detail"),
    path("api/profile/", views.profile_api, name="profile_api"),
    path("api/profile/image/", views.profile_image_api, name="profile_image_api"),
    path("", main_spa, name="spa"),
]
