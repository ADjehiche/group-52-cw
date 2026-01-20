from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest, JsonResponse
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth import get_user_model

from .models import Item
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
    POST /api/items/
    Create a new auction item for the authenticated user.
    """
    if request.method == "GET":
        items = Item.objects.all().order_by("-id")
        return JsonResponse(
            {
                "items": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "description": item.description,
                        "starting_price": str(item.starting_price),
                        "image_url": request.build_absolute_uri(item.image.url) if item.image else None,
                        "ends_at": item.ends_at.isoformat(),
                        "owner_id": item.owner_id,
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

    # Handle FormData with file upload
    data = request.POST
    image_file = request.FILES.get("image")

    errors: dict[str, str] = {}

    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    ends_at_raw = (data.get("ends_at") or "").strip()
    starting_price_raw = (data.get("starting_price") or "").strip()

    if not title:
        errors["title"] = "Title is required."

    # Parse money
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

    # Parse datetime
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

    item = Item(
        owner=request.user,
        title=title,
        description=description,
        starting_price=starting_price,  # type: ignore[arg-type]
        ends_at=ends_at,  # type: ignore[arg-type]
    )
    
    if image_file:
        item.image = image_file

    # Runs model-level validation (including your clean()).
    try:
        item.full_clean()
        item.save()
    except ValidationError as exc:
        # Convert Django ValidationError to a simple JSON shape
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
            "image_url": request.build_absolute_uri(item.image.url) if item.image else None,
            "ends_at": item.ends_at.isoformat(),
            "owner_id": item.owner_id,
        },
        status=201,
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
    """Serialize the current user for the profile page."""
    u = request.user
    return {
        "id": u.pk,
        "username": u.username,
        "email": u.email,
        "date_of_birth": u.date_of_birth.isoformat() if getattr(u, "date_of_birth", None) else None,
        "profile_image_url": (
            request.build_absolute_uri(u.profile_image.url)
            if getattr(u, "profile_image", None)
            else None
        ),
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

