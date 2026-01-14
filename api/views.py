from __future__ import annotations

from typing import Iterable

from django.db.models import Q
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

    items_qs = Item.objects.filter(ends_at__gt=timezone.now())
    if query:
        items_qs = items_qs.filter(Q(title__icontains=query) | Q(description__icontains=query))

    items = items_qs.order_by("-id")
    return JsonResponse({"items": _serialize_items(items)}, status=200)


def main_spa(request: HttpRequest) -> HttpResponse:
    """Serve the built Vue SPA entry point."""
    return render(request, "api/spa/index.html", {})
