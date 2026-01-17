from __future__ import annotations

from typing import Iterable

from django.db.models import Case, IntegerField, Q, When
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone

from .models import Item


def _serialize_items(items: Iterable[Item]) -> list[dict[str, object]]:
    """Serialize Item queryset into a simple JSON-safe list."""
    return [
        {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "starting_price": str(item.starting_price),
            "image_url": item.image_url,
            "ends_at": item.ends_at.isoformat(),
            "owner_id": item.owner_id,
        }
        for item in items
    ]


def items_collection(request: HttpRequest) -> JsonResponse:
    """
    GET: return active items, optionally filtered by keyword in title/description.
    Only items whose `ends_at` is in the future are returned (active auctions).
    """
    if request.method != "GET":
        return JsonResponse({"detail": "Method not allowed."}, status=405)

    query = (request.GET.get("q") or "").strip()
    sort_param = (request.GET.get("sort") or "ending-soon").strip()

    sort_map: dict[str, tuple[str, ...]] = {
        "ending-soon": ("ends_at",),
        "newest": ("-created_at",),
        "price-asc": ("starting_price",),
        "price-desc": ("-starting_price",),
    }

    items_qs = Item.objects.filter(ends_at__gt=timezone.now())
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
            items_qs = items_qs.order_by("-title_match", "-desc_match", "-created_at")
        else:
            items_qs = items_qs.order_by(*sort_map.get(sort_param, sort_map["ending-soon"]))
    else:
        items_qs = items_qs.order_by(*sort_map.get(sort_param, sort_map["ending-soon"]))

    items = items_qs
    return JsonResponse({"items": _serialize_items(items)}, status=200)


def main_spa(request: HttpRequest) -> HttpResponse:
    """Serve the built Vue SPA entry point."""
    return render(request, "api/spa/index.html", {})
