from django.urls import path, re_path

from .views import (
    api_logout,
    auth_status,
    follow_user,
    follower_stats,
    item_detail,
    item_questions_list_or_create,
    items_collection,
    like_answer,
    like_question,
    main_spa,
    place_bid,
    profile_api,
    profile_image_api,
    question_answer,
    user_followers,
    user_following,
)

urlpatterns = [
    path("api/items/", items_collection, name="api-items-collection"),
    path("api/items/<int:item_id>/", item_detail, name="api-item-detail"),
    path("api/items/<int:item_id>/questions/", item_questions_list_or_create, name="item_questions"),
    path("api/items/<int:item_id>/bid/", place_bid, name="place_bid"),
    path("api/questions/<int:question_id>/answer/", question_answer, name="question_answer"),
    path("api/questions/<int:question_id>/like/", like_question, name="like_question"),
    path("api/questions/<int:question_id>/answer/like/", like_answer, name="like_answer"),
    path("api/users/<int:user_id>/follow/", follow_user, name="follow_user"),
    path("api/users/<int:user_id>/followers/", user_followers, name="user_followers"),
    path("api/users/<int:user_id>/following/", user_following, name="user_following"),
    path("api/profile/follower-stats/", follower_stats, name="follower_stats"),
    path("api/logout/", api_logout, name="api_logout"),
    path("api/auth/status/", auth_status, name="auth_status"),
    path("api/profile/", profile_api, name="profile_api"),
    path("api/profile/image/", profile_image_api, name="profile_image_api"),
    # Catch-all for SPA routes (must be last)
    re_path(r"^.*$", main_spa, name="spa"),
]


