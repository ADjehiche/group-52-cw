from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any

from django.contrib.auth import login, logout
from django.core.exceptions import ValidationError
from django.http import HttpRequest, JsonResponse
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from .models import Item, ItemImage
from .forms import SignUpForm

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
    List all auction items with their images.
    
    POST /api/items/
    Create a new auction item for the authenticated user with multiple images (up to 8).
    """
    if request.method == "GET":
        items = Item.objects.all().order_by("-id").prefetch_related('images')
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

    # Handle FormData with multiple file uploads
    data = request.POST
    image_files = request.FILES.getlist("images")  # Support multiple images

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

    # Validate number of images (max 8)
    if len(image_files) > 8:
        return JsonResponse({"errors": {"images": "Maximum 8 images allowed."}}, status=400)

    item = Item(
        owner=request.user,
        title=title,
        description=description,
        starting_price=starting_price,  # type: ignore[arg-type]
        ends_at=ends_at,  # type: ignore[arg-type]
    )

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

    # Create ItemImage instances for each uploaded file
    created_images = []
    for idx, image_file in enumerate(image_files):
        try:
            item_image = ItemImage(
                item=item,
                image=image_file,
                order=idx
            )
            item_image.full_clean()
            item_image.save()
            created_images.append(item_image)
        except ValidationError as exc:
            # If image validation fails, return error
            field_errors = {}
            for field, msgs in exc.message_dict.items():
                field_errors[f"image_{idx}_{field}"] = msgs[0] if msgs else "Invalid value."
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

