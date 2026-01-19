from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any

from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import HttpRequest, JsonResponse
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST



from .models import Item, ItemImage


def signup(request: HttpRequest) -> HttpResponse:
    """
    GET: show signup form
    POST: create user and log them in
    """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")
    else:
        form = UserCreationForm()

    return render(request, "registration/signup.html", {"form": form})




def items_collection(request: HttpRequest) -> JsonResponse:
    """
    POST /api/items/
    Create a new auction item for the authenticated user.
    """
    if request.method == "GET":
        items = Item.objects.all().prefetch_related("images").order_by("-id")
        return JsonResponse(
            {
                "items": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "description": item.description,
                        "starting_price": str(item.starting_price),
                        "image_url": item.image_url,
                        "image_urls": [
                            request.build_absolute_uri(img.image_file.url)
                            if img.image_file
                            else img.image_url
                            for img in item.images.all()
                        ]
                        or ([item.image_url] if item.image_url else []),
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

    data: dict[str, Any] = {}

    # Accept JSON (Vue fetch) or multipart form-data (uploads)
    content_type = request.headers.get("Content-Type", "")
    if "application/json" in content_type:
        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"detail": "Invalid JSON body."}, status=400)
    else:
        data = request.POST.dict()

    errors: dict[str, str] = {}

    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    image_url = (data.get("image_url") or "").strip()
    image_urls_raw = data.get("image_urls")
    image_files = request.FILES.getlist("images")
    ends_at_raw = (data.get("ends_at") or "").strip()
    starting_price_raw = (data.get("starting_price") or "").strip()

    if not title:
        errors["title"] = "Title is required."

    image_urls: list[str] = []
    if isinstance(image_urls_raw, list):
        image_urls = [str(url).strip() for url in image_urls_raw if str(url).strip()]
    elif image_urls_raw is not None:
        errors["image_urls"] = "Image URLs must be a list."
    elif image_url:
        image_urls = [image_url]

    if image_urls:
        if len(image_urls) > 8:
            errors["image_urls"] = "You can upload up to 8 images."
        else:
            validator = URLValidator()
            for url in image_urls:
                try:
                    validator(url)
                except ValidationError:
                    errors["image_urls"] = "All image URLs must be valid URLs."
                    break

    if image_files:
        if len(image_files) > 8:
            errors["images"] = "You can upload up to 8 images."

    if image_urls and image_files:
        if len(image_urls) + len(image_files) > 8:
            errors["images"] = "You can upload up to 8 images."

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
        image_url=image_urls[0] if image_urls else "",
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

    images_to_create: list[ItemImage] = []
    position = 0
    for url in image_urls:
        images_to_create.append(ItemImage(item=item, image_url=url, position=position))
        position += 1

    for uploaded in image_files:
        images_to_create.append(ItemImage(item=item, image_file=uploaded, position=position))
        position += 1

    if images_to_create:
        ItemImage.objects.bulk_create(images_to_create)

    if images_to_create and not item.image_url:
        first_image = images_to_create[0]
        if first_image.image_file:
            item.image_url = request.build_absolute_uri(first_image.image_file.url)
        else:
            item.image_url = first_image.image_url
        item.save(update_fields=["image_url"])

    return JsonResponse(
        {
            "id": item.pk,
            "title": item.title,
            "description": item.description,
            "starting_price": str(item.starting_price),
            "image_url": item.image_url,
            "image_urls": [
                request.build_absolute_uri(img.image_file.url) if img.image_file else img.image_url
                for img in item.images.all()
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

