from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any

from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.http import HttpRequest, JsonResponse
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST



from .models import Item, ItemQuestion, ItemAnswer


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

def api_questions(request: HttpRequest) -> JsonResponse:
    """Get a list of questions. For a specific user, pass the user_id as a query parameter."""
    user_id = request.GET.get("user_id")
    if user_id:
        questions = Question.objects.filter(author_id=user_id).order_by("-created_at")
    else:
        questions = Question.objects.all().order_by("-created_at")
    return JsonResponse(
        {
            "questions": [
                {
                    "id": question.id,
                    "title": question.title,
                    "content": question.content,
                    "author": question.author.username,
                    "created_at": question.created_at.isoformat(),
                    "updated_at": question.updated_at.isoformat(),
                    "likes": question.likes,
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
        questions = ItemQuestion.objects.filter(item=item).select_related("asker", "answer")
        return JsonResponse(
            {
                "questions": [
                    {
                        "id": q.id,
                        "question_text": q.question_text,
                        "asker": q.asker.username,
                        "asker_id": q.asker_id,
                        "created_at": q.created_at.isoformat(),
                        "answer": {
                            "answer_text": q.answer.answer_text,
                            "created_at": q.answer.created_at.isoformat(),
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
            return JsonResponse({"errors": {"question_text": "Invalid JSON."}}, status=400)
        
        question_text = (data.get("question_text") or "").strip()
        
        if not question_text:
            return JsonResponse({"errors": {"question_text": "Question text is required."}}, status=400)
        
        # Create the question
        question = ItemQuestion.objects.create(
            item=item,
            asker=request.user,
            question_text=question_text,
        )
        
        return JsonResponse(
            {
                "id": question.id,
                "question_text": question.question_text,
                "asker": question.asker.username,
                "asker_id": question.asker_id,
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
        question = ItemQuestion.objects.select_related("item").get(pk=question_id)
    except ItemQuestion.DoesNotExist:
        return JsonResponse({"detail": "Question not found."}, status=404)
    
    # Permission check: only item owner can answer
    if question.item.owner_id != request.user.pk:
        return JsonResponse({"detail": "Only the item owner can answer this question."}, status=403)
    
    # Parse JSON body
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"errors": {"answer_text": "Invalid JSON."}}, status=400)
    
    answer_text = (data.get("answer_text") or "").strip()
    
    if not answer_text:
        return JsonResponse({"errors": {"answer_text": "Answer text is required."}}, status=400)
    
    # Create or update the answer
    answer, created = ItemAnswer.objects.update_or_create(
        question=question,
        defaults={"answer_text": answer_text},
    )
    
    return JsonResponse(
        {
            "id": answer.id,
            "question_id": question.id,
            "answer_text": answer.answer_text,
            "created_at": answer.created_at.isoformat(),
        },
        status=201 if created else 200,
    )