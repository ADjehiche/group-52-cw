from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest, JsonResponse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.contrib.auth import get_user_model

from .models import Answer, AnswerLike, Bid, Follow, Item, ItemImage, Question, QuestionLike
from django.db import transaction
from django.db.models import Case, Count, IntegerField, Q, When

from .forms import SignUpForm

User = get_user_model()



def signup(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")
    else:
        form = SignUpForm()

    return render(request, "registration/signup.html", {"form": form})


def items_collection(request: HttpRequest) -> JsonResponse:
    """
    GET /api/items/
    List all auction items.

    POST /api/items/
    Create a new auction item for the authenticated user.
    """
    if request.method == "GET":
        query = (request.GET.get("q") or "").strip()
        sort_param = (request.GET.get("sort") or "ending-soon").strip()

        sort_map: dict[str, tuple[str, ...]] = {
            "ending-soon": ("ends_at",),
            "newest": ("-created_at",),
            "price-asc": ("starting_price",),
            "price-desc": ("-starting_price",),
        }

        items_qs = Item.objects.filter(ends_at__gt=timezone.now()).prefetch_related("images")
        if query:
            items_qs = items_qs.annotate(
                title_match=Case(
                    When(title__icontains=query, then=1),
                    default=0,
                    output_field=IntegerField(),
                ),
                desc_match=Case(
                    When(description__icontains=query, then=1),
                    default=0,
                    output_field=IntegerField(),
                ),
            ).filter(Q(title_match=1) | Q(desc_match=1))

            if sort_param == "relevance":
                items_qs = items_qs.order_by("-title_match", "-desc_match", "-id")
            else:
                items_qs = items_qs.order_by(*sort_map.get(sort_param, sort_map["ending-soon"]))
        else:
            items_qs = items_qs.order_by(*sort_map.get(sort_param, sort_map["ending-soon"]))

        items = items_qs
        return JsonResponse(
            {
                "items": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "description": item.description,
                        "starting_price": str(item.starting_price),
                        "images": [
                            {
                                "id": img.id,
                                "url": request.build_absolute_uri(img.image.url),
                                "order": img.order,
                            }
                            for img in item.images.all()
                        ],
                        "ends_at": item.ends_at.isoformat(),
                        "owner_id": item.owner_id,
                        "time_remaining_seconds": max(0, (item.ends_at - timezone.now()).total_seconds()),
                    }
                    for item in items
                ]
            },
            status=200,
        )

    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed."}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=401)

    data = request.POST
    image_files = request.FILES.getlist("images")

    errors: dict[str, str] = {}

    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    ends_at_raw = (data.get("ends_at") or "").strip()
    starting_price_raw = (data.get("starting_price") or "").strip()

    if not title:
        errors["title"] = "Title is required."

    starting_price: Decimal | None = None
    if not starting_price_raw:
        errors["starting_price"] = "Starting price is required."
    else:
        try:
            starting_price = Decimal(starting_price_raw)
            if starting_price < 0:
                errors["starting_price"] = "Starting price must be 0 or more."
        except (InvalidOperation, ValueError):
            errors["starting_price"] = "Starting price must be a valid number."

    ends_at = None
    if not ends_at_raw:
        errors["ends_at"] = "End date/time is required."
    else:
        ends_at = parse_datetime(ends_at_raw)
        if ends_at is None:
            errors["ends_at"] = "Invalid datetime format."
        else:
            if timezone.is_naive(ends_at):
                ends_at = timezone.make_aware(ends_at, timezone.get_current_timezone())
            if ends_at <= timezone.now():
                errors["ends_at"] = "Auction end time must be in the future."

    if errors:
        return JsonResponse({"errors": errors}, status=400)

    if len(image_files) > 8:
        return JsonResponse({"errors": {"images": "Maximum 8 images allowed."}}, status=400)

    item = Item(
        owner=request.user,
        title=title,
        description=description,
        starting_price=starting_price,  # type: ignore[arg-type]
        ends_at=ends_at,  # type: ignore[arg-type]
    )
    created_images = []
    try:
        with transaction.atomic():
            item.full_clean()
            item.save()
            for idx, image_file in enumerate(image_files):
                item_image = ItemImage(
                    item=item,
                    image=image_file,
                    order=idx,
                )
                item_image.full_clean()
                item_image.save()
                created_images.append(item_image)
    except ValidationError as exc:
        field_errors: dict[str, str] = {}
        for field, msgs in exc.message_dict.items():
            field_errors[field] = msgs[0] if msgs else "Invalid value."
        return JsonResponse({"errors": field_errors}, status=400)

    return JsonResponse(
        {
            "id": item.pk,
            "title": item.title,
            "description": item.description,
            "starting_price": str(item.starting_price),
            "images": [
                {
                    "id": img.id,
                    "url": request.build_absolute_uri(img.image.url),
                    "order": img.order,
                }
                for img in created_images
            ],
            "ends_at": item.ends_at.isoformat(),
            "owner_id": item.owner_id,
        },
        status=201,
    )


@require_GET
def item_detail(request: HttpRequest, item_id: int) -> JsonResponse:
    """Return a single item."""
    item = get_object_or_404(Item.objects.prefetch_related("images"), pk=item_id)
    
    highest_bid = item.bids.order_by("-amount").first()
    highest_bid_data = None
    if highest_bid:
        highest_bid_data = {
            "amount": str(highest_bid.amount),
            "bidder_id": highest_bid.bidder_id,
        }

    
    # Check if current user is following the owner
    is_following_owner = False
    if request.user.is_authenticated and request.user.pk != item.owner_id:
        is_following_owner = Follow.objects.filter(follower=request.user, followee=item.owner).exists()
    
    owner_avatar_url = None
    if item.owner.profile_image:
        owner_avatar_url = request.build_absolute_uri(item.owner.profile_image.url)

    return JsonResponse(
        {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "starting_price": str(item.starting_price),
            "images": [
                {
                    "id": img.id,
                    "url": request.build_absolute_uri(img.image.url),
                    "order": img.order,
                }
                for img in item.images.all()
            ],
            "ends_at": item.ends_at.isoformat(),
            "owner_id": item.owner_id,
            "owner_username": item.owner.username,
            "owner_avatar_url": owner_avatar_url,
            "is_following_owner": is_following_owner,
            "highest_bid": highest_bid_data,
            "time_remaining_seconds": max(0, (item.ends_at - timezone.now()).total_seconds()),
        },
        status=200,
    )

@ensure_csrf_cookie
def main_spa(request: HttpRequest) -> HttpResponse:
    """
    Serve the built Vue SPA (production build).
    """
    return render(request, "api/spa/index.html")


@require_POST
def api_logout(request: HttpRequest) -> JsonResponse:
    """Log out the user and respond with a simple JSON body."""
    logout(request)
    return JsonResponse({"ok": True})


def auth_status(request: HttpRequest) -> JsonResponse:
    """Return whether the current session is authenticated."""
    if request.user.is_authenticated:
        return JsonResponse(
            {
                "authenticated": True,
                "user": {
                    "id": request.user.pk,
                    "username": request.user.username,
                    "is_staff": request.user.is_staff,
                },
            }
        )
    return JsonResponse({"authenticated": False, "user": None})

def _profile_payload(request: HttpRequest) -> dict[str, Any]:
    u = request.user

    profile_url = None
    try:
        if getattr(u, "profile_image", None) and u.profile_image:
            profile_url = u.profile_image.url 
    except (ValueError, OSError) as exc:
        profile_url = None

    return {
        "id": u.pk,
        "username": u.username,
        "email": u.email,
        "date_of_birth": u.date_of_birth.isoformat() if getattr(u, "date_of_birth", None) else None,
        "profile_image_url": profile_url,
    }


@login_required
@require_http_methods(["GET", "PATCH", "POST"])
def profile_api(request: HttpRequest) -> JsonResponse:
    """
    GET  /api/profile/        -> current profile
    PATCH/POST /api/profile/  -> update email and/or date_of_birth (JSON)
    """
    if request.method == "GET":
        return JsonResponse(_profile_payload(request), status=200)

    try:
        raw = request.body.decode("utf-8") if request.body else "{}"
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"errors": {"__all__": "Invalid JSON."}}, status=400)

    user = request.user
    errors: dict[str, str] = {}

    # Email
    if "email" in payload:
        email = (payload.get("email") or "").strip().lower()
        if not email:
            errors["email"] = "Email is required."
        elif User.objects.filter(email=email).exclude(pk=user.pk).exists():
            errors["email"] = "This email is already in use."
        else:
            user.email = email

    # Date of birth
    if "date_of_birth" in payload:
        dob_raw = (payload.get("date_of_birth") or "").strip()
        if not dob_raw:
            user.date_of_birth = None
        else:
            dob = parse_date(dob_raw)
            if dob is None:
                errors["date_of_birth"] = "Invalid date format. Use YYYY-MM-DD."
            else:
                user.date_of_birth = dob

    if errors:
        return JsonResponse({"errors": errors}, status=400)

    try:
        user.full_clean()
        user.save()
    except ValidationError as exc:
        field_errors: dict[str, str] = {
            field: (msgs[0] if msgs else "Invalid value.")
            for field, msgs in exc.message_dict.items()
        }
        return JsonResponse({"errors": field_errors}, status=400)

    return JsonResponse(_profile_payload(request), status=200)


@login_required
@require_POST
def profile_image_api(request: HttpRequest) -> JsonResponse:
    """POST /api/profile/image/ -> upload profile image (multipart/form-data)."""
    image_file = request.FILES.get("profile_image")
    if not image_file:
        return JsonResponse({"errors": {"profile_image": "Please choose an image to upload."}}, status=400)

    user = request.user
    user.profile_image = image_file

    try:
        user.full_clean()
        user.save()
    except ValidationError as exc:
        field_errors: dict[str, str] = {
            field: (msgs[0] if msgs else "Invalid value.")
            for field, msgs in exc.message_dict.items()
        }
        return JsonResponse({"errors": field_errors}, status=400)

    return JsonResponse(_profile_payload(request), status=200)

def api_questions(request: HttpRequest) -> JsonResponse:
    """Get a list of questions. For a specific user, pass the user_id as a query parameter."""
    user_id = request.GET.get("user_id")
    if user_id:
        questions = Question.objects.filter(author_id=user_id).select_related('item', 'author').order_by("-created_at")
    else:
        questions = Question.objects.all().select_related('item', 'author').order_by("-created_at")
    return JsonResponse(
        {
            "questions": [
                {
                    "id": question.id,
                    "content": question.content,
                    "author": question.author.username,
                    "created_at": question.created_at.isoformat(),
                    "item_id": question.item_id,
                    "item_title": question.item.title,
                }
                for question in questions
            ]
        },
        status=200,
    )


def item_questions_list_or_create(request: HttpRequest, item_id: int) -> JsonResponse:
    """
    GET: List all questions for an item (public)
    POST: Create a new question for an item (authenticated users only)
    """
    # Check if item exists
    try:
        item = Item.objects.get(pk=item_id)
    except Item.DoesNotExist:
        return JsonResponse({"detail": "Item not found."}, status=404)
    
    if request.method == "GET":
        # Public - anyone can view questions
        questions = Question.objects.filter(item=item).select_related("author", "answer")
        return JsonResponse(
            {
                "questions": [
                    {
                        "id": q.id,
                        "content": q.content,
                        "author": q.author.username,
                        "author_id": q.author_id,
                        "author_avatar_url": request.build_absolute_uri(q.author.profile_image.url) if q.author.profile_image else None,
                        "created_at": q.created_at.isoformat(),
                        "answer": {
                            "content": q.answer.content,
                            "created_at": q.answer.created_at.isoformat(),
                            "author_avatar_url": request.build_absolute_uri(q.item.owner.profile_image.url) if q.item.owner.profile_image else None, 
                        } if hasattr(q, "answer") else None,
                    }
                    for q in questions
                ]
            },
            status=200,
        )
    
    if request.method == "POST":
        # Authentication required
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required."}, status=401)
        
        # Parse JSON body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"errors": {"content": "Invalid JSON."}}, status=400)
        
        content = (data.get("content") or "").strip()
        
        if not content:
            return JsonResponse({"errors": {"content": "Question content is required."}}, status=400)
        
        # Create the question
        question = Question.objects.create(
            item=item,
            author=request.user,
            content=content,
        )
        
        return JsonResponse(
            {
                "id": question.id,
                "content": question.content,
                "author": question.author.username,
                "author_id": question.author_id,
                "author_avatar_url": request.build_absolute_uri(question.author.profile_image.url) if question.author.profile_image else None,
                "created_at": question.created_at.isoformat(),
                "answer": None,
            },
            status=201,
        )
    
    return JsonResponse({"detail": "Method not allowed."}, status=405)


def question_answer(request: HttpRequest, question_id: int) -> JsonResponse:
    """
    POST: Answer a question (item owner only)
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed."}, status=405)
    
    # Authentication required
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=401)
    
    # Check if question exists
    try:
        question = Question.objects.select_related("item").get(pk=question_id)
    except Question.DoesNotExist:
        return JsonResponse({"detail": "Question not found."}, status=404)
    
    # Permission check: only item owner can answer
    if question.item.owner_id != request.user.pk:
        return JsonResponse({"detail": "Only the item owner can answer this question."}, status=403)
    
    # Parse JSON body
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"errors": {"content": "Invalid JSON."}}, status=400)
    
    content = (data.get("content") or "").strip()
    
    if not content:
        return JsonResponse({"errors": {"content": "Answer content is required."}}, status=400)
    
    # Create or update the answer
    answer, created = Answer.objects.update_or_create(
        question=question,
        defaults={"content": content, "author": request.user},
    )
    
    return JsonResponse(
        {
            "id": answer.id,
            "question_id": question.id,
            "content": answer.content,
            "created_at": answer.created_at.isoformat(),
        },
        status=201 if created else 200,
    )
# New API endpoints for followers and likes

@login_required
@require_http_methods(["POST", "DELETE"])
def follow_user(request: HttpRequest, user_id: int) -> JsonResponse:
    """
    POST: Follow a user
    DELETE: Unfollow a user
    """
    # Check if target user exists
    try:
        followee = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse({"detail": "User not found."}, status=404)
    
    # Cannot follow yourself
    if request.user.pk == user_id:
        return JsonResponse({"detail": "You cannot follow yourself."}, status=400)
    
    if request.method == "POST":
        # Create follow relationship
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            followee=followee
        )
        
        if not created:
            return JsonResponse({"detail": "You are already following this user."}, status=400)
        
        return JsonResponse({
            "id": follow.id,
            "follower_id": request.user.pk,
            "followee_id": followee.pk,
            "created_at": follow.created_at.isoformat(),
        }, status=201)
    
    if request.method == "DELETE":
        # Delete follow relationship
        try:
            follow = Follow.objects.get(follower=request.user, followee=followee)
            follow.delete()
            return JsonResponse({"detail": "Unfollowed successfully."}, status=200)
        except Follow.DoesNotExist:
            return JsonResponse({"detail": "You are not following this user."}, status=400)
    
    return JsonResponse({"detail": "Method not allowed."}, status=405)


@require_GET
def user_followers(request: HttpRequest, user_id: int) -> JsonResponse:
    """GET: List all followers of a user"""
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse({"detail": "User not found."}, status=404)
    
    followers = Follow.objects.filter(followee=user).select_related("follower")
    
    return JsonResponse({
        "user_id": user_id,
        "follower_count": followers.count(),
        "followers": [
            {
                "id": f.follower.pk,
                "username": f.follower.username,
                "followed_at": f.created_at.isoformat(),
            }
            for f in followers
        ]
    }, status=200)


@require_GET
def user_following(request: HttpRequest, user_id: int) -> JsonResponse:
    """GET: List all users that this user is following"""
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse({"detail": "User not found."}, status=404)
    
    following = Follow.objects.filter(follower=user).select_related("followee")
    
    return JsonResponse({
        "user_id": user_id,
        "following_count": following.count(),
        "following": [
            {
                "id": f.followee.pk,
                "username": f.followee.username,
                "followed_at": f.created_at.isoformat(),
            }
            for f in following
        ]
    }, status=200)


@login_required
@require_GET
def follower_stats(request: HttpRequest) -> JsonResponse:
    """GET: Get follower stats for the current user"""
    user = request.user
    
    follower_count = Follow.objects.filter(followee=user).count()
    following_count = Follow.objects.filter(follower=user).count()
    
    return JsonResponse({
        "follower_count": follower_count,
        "following_count": following_count,
    }, status=200)


@login_required
@require_POST
def like_question(request: HttpRequest, question_id: int) -> JsonResponse:
    """POST: Like/unlike a question (toggle)"""
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return JsonResponse({"detail": "Question not found."}, status=404)
    
    # Toggle like
    like, created = QuestionLike.objects.get_or_create(
        user=request.user,
        question=question
    )
    
    if not created:
        # Unlike
        like.delete()
        return JsonResponse({
            "liked": False,
            "like_count": QuestionLike.objects.filter(question=question).count()
        }, status=200)
    
    # Like
    return JsonResponse({
        "liked": True,
        "like_count": QuestionLike.objects.filter(question=question).count()
    }, status=201)


@login_required
@require_POST
def like_answer(request: HttpRequest, question_id: int) -> JsonResponse:
    """POST: Like/unlike an answer (toggle) - accessed via question ID"""
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return JsonResponse({"detail": "Question not found."}, status=404)
    
    # Check if answer exists
    if not hasattr(question, "answer"):
        return JsonResponse({"detail": "This question has not been answered yet."}, status=404)
    
    answer = question.answer
    
    # Toggle like
    like, created = AnswerLike.objects.get_or_create(
        user=request.user,
        answer=answer
    )
    
    if not created:
        # Unlike
        like.delete()
        return JsonResponse({
            "liked": False,
            "like_count": AnswerLike.objects.filter(answer=answer).count()
        }, status=200)
    
    # Like
    return JsonResponse({
        "liked": True,
        "like_count": AnswerLike.objects.filter(answer=answer).count()
    }, status=201)

@login_required
@require_POST
def place_bid(request: HttpRequest, item_id: int) -> JsonResponse:
    """POST /api/items/<id>/bid/ -> Place a bid on an item."""
    try:
        item = Item.objects.get(pk=item_id)
    except Item.DoesNotExist:
        return JsonResponse({"detail": "Item not found."}, status=404)

    if item.ends_at <= timezone.now():
        return JsonResponse({"detail": "Auction has ended."}, status=400)

    try:
        data = json.loads(request.body)
        amount_str = str(data.get("amount", "")).strip()
        amount = Decimal(amount_str)
    except (json.JSONDecodeError, ValueError, InvalidOperation):
        return JsonResponse({"errors": {"amount": "Invalid amount."}}, status=400)

    bid = Bid(item=item, bidder=request.user, amount=amount)

    try:
        bid.clean()  # Run model validation (checks > highest bid, etc)
        bid.save()
    except ValidationError as exc:
        # Extract message from validation error
        msg = "Invalid bid."
        if hasattr(exc, 'error_dict'):
             # If it's a dict of errors, grab the first one or specific field
            errors = exc.message_dict
            if 'amount' in errors:
                msg = errors['amount'][0]
            elif '__all__' in errors:
                msg = errors['__all__'][0]
        elif hasattr(exc, "message"):
            msg = exc.message
        elif hasattr(exc, "messages"):
            msg = exc.messages[0]
        
        return JsonResponse({"errors": {"amount": msg}}, status=400)

    return JsonResponse(
        {
            "id": bid.id,
            "bidder": bid.bidder.username,
            "amount": str(bid.amount),
            "created_at": bid.created_at.isoformat(),
        },
        status=201,
    )
