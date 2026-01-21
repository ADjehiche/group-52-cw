
from __future__ import annotations

from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Max, Q
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom user model
    - email: already present on AbstractUser; we enforce non-blank + unique
    - date_of_birth: new
    - profile_image: new
    """
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_image = models.ImageField(upload_to="profile_images/", blank=True, null=True)
    
    # Fix clash with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='api_user_set',
        related_query_name='api_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='api_user_set',
        related_query_name='api_user',
    )

    def __str__(self) -> str:
        return self.username

class PageView(models.Model):
    count = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"Page view count: {self.count}"


class Question(models.Model):
    item = models.ForeignKey('Item', on_delete=models.CASCADE, related_name='questions')
    content: str = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='questions')
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"Question on {self.item.title}: {preview}"


class Answer(models.Model):
    question: Question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='answer')
    content: str = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='answers')
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        preview = self.question.content[:30] + '...' if len(self.question.content) > 30 else self.question.content
        return f"Answer to '{preview}'" 
    
class Item(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="items",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    starting_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    ends_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(starting_price__gte=0),
                name="item_starting_price_gte_0",
            ),
        ]

    def clean(self) -> None:
        super().clean()

        # Auction must end in the future when creating/updating an item.
        if self.ends_at <= timezone.now():
            raise ValidationError({"ends_at": "Auction end time must be in the future."})

    def __str__(self) -> str:
        return self.title


class ItemImage(models.Model):
    """Model for storing multiple images per auction item (max 8)."""
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="items/")
    order = models.PositiveSmallIntegerField(default=0, help_text="Display order of the image")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Item Image"
        verbose_name_plural = "Item Images"

    def clean(self) -> None:
        super().clean()

        # Limit to maximum 8 images per item
        if self.item_id:
            existing_count = ItemImage.objects.filter(item=self.item).exclude(pk=self.pk).count()
            if existing_count >= 8:
                raise ValidationError("An item can have a maximum of 8 images.")

    def __str__(self) -> str:
        return f"Image {self.order} for {self.item.title}"


class Bid(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="bids",
    )
    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bids",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="bid_amount_gt_0",
            ),
        ]

    def clean(self) -> None:
        super().clean()

        now = timezone.now()

        # No bids allowed after the auction ends.
        if self.item.ends_at <= now:
            raise ValidationError("You cannot bid after the auction has ended.")

        # Enforce "bid must be greater than current highest bid" (or starting price if no bids yet).
        highest = (
            Bid.objects.filter(item=self.item)
            .exclude(pk=self.pk)
            .aggregate(Max("amount"))
            .get("amount__max")
        )

        minimum_required = highest if highest is not None else self.item.starting_price
        if self.amount <= minimum_required:
            raise ValidationError(f"Bid must be greater than £{minimum_required}.")

    def __str__(self) -> str:
        return f"£{self.amount} on item {self.item_id}"
