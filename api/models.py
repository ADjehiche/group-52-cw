from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Max, Q
from django.utils import timezone


class PageView(models.Model):
    count = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"Page view count: {self.count}"


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
    image = models.ImageField(upload_to="items/", blank=True, null=True)
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
