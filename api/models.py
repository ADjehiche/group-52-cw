"""Django models for the CBay auction application.

This module defines all database models for the auction platform:
- User: Custom user model with profile extensions
- Item: Auction item listings
- ItemImage: Multiple images per item (max 8)
- Bid: User bids on auction items with validation
- Question/Answer: Q&A system for items
- Follow: Social following between users
- QuestionLike/AnswerLike: Engagement tracking for Q&A

All models include comprehensive validation and business rule enforcement.
"""
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
    """Custom user model extending Django's AbstractUser.
    
    Adds profile fields beyond the default Django user:
    - email: Made unique and required (overriding AbstractUser's optional email)
    - date_of_birth: Optional user birthdate
    - profile_image: User profile picture stored in media/profile_images/
    
    Related managers:
        items: All auction items created by this user
        bids: All bids placed by this user
        questions: All questions asked by this user
        answers: All answers provided by this user (as seller)
        following: Users this user follows
        followers: Users following this user
    """
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_image = models.ImageField(
        upload_to="profile_images/",
        blank=True,
        null=True,
    )
    
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
    """Simple counter model for tracking page views (legacy/utility).
    
    Attributes:
        count: Integer counter for total page views
    """
    count = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"Page view count: {self.count}"


class Question(models.Model):
    """User questions about auction items.
    
    Allows authenticated users to ask sellers questions about specific items.
    Each question can have one Answer from the item owner.
    
    Attributes:
        item: The auction item this question is about
        content: The question text
        author: User who asked the question
        created_at: Timestamp when question was posted
    
    Related managers:
        answer: The seller's answer to this question (OneToOne)
        likes: Users who liked this question
    """
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
    """Seller answers to user questions about their auction items.
    
    Each Answer is linked to exactly one Question (OneToOne relationship).
    Only the item owner can answer questions about their items.
    
    Attributes:
        question: The question being answered
        content: The answer text
        author: User who provided the answer (should be item owner)
        created_at: Timestamp when answer was posted
    
    Related managers:
        likes: Users who liked this answer
    """
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
    """Auction item listing model.
    
    Represents an item being auctioned with a starting price and end time.
    Enforces business rules via clean() method and database constraints.
    
    Attributes:
        owner: User who created this auction
        title: Item title (max 200 chars)
        description: Detailed item description
        starting_price: Minimum bid amount (must be >= 0)
        ends_at: Auction end date/time (must be in future when created)
        created_at: Timestamp when item was listed
        winner_notified: Flag indicating if auction close emails were sent
    
    Related managers:
        images: Item photos (max 8, ordered)
        bids: All bids placed on this item
        questions: User questions about this item
    
    Validation:
        - starting_price must be >= 0 (database constraint + validator)
        - ends_at must be in the future (model clean() method)
    """
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
    winner_notified = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(starting_price__gte=0),
                name="item_starting_price_gte_0",
            ),
        ]

    def clean(self) -> None:
        """Validate that auction end time is in the future.
        
        Raises:
            ValidationError: If ends_at is not in the future
        """
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
        """Validate maximum image limit per item.
        
        Ensures an item doesn't exceed 8 images total.
        
        Raises:
            ValidationError: If adding this image would exceed 8 images per item
        """
        super().clean()

        # Limit to maximum 8 images per item
        if self.item_id:
            existing_count = ItemImage.objects.filter(item=self.item).exclude(pk=self.pk).count()
            if existing_count >= 8:
                raise ValidationError("An item can have a maximum of 8 images.")

    def __str__(self) -> str:
        return f"Image {self.order} for {self.item.title}"



class Bid(models.Model):
    """User bid on an auction item.
    
    Enforces auction bidding rules:
    - Bid must be greater than current highest bid (or starting price)
    - Cannot bid after auction has ended
    - Bid amount must be > 0
    
    Attributes:
        item: The auction item being bid on
        bidder: User placing the bid
        amount: Bid amount in GBP (must be > 0)
        created_at: Timestamp when bid was placed
    
    Validation:
        - amount must be > 0 (database constraint + validator)
        - amount must exceed current highest bid or starting price (clean())
        - auction must not have ended (clean())
    """
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
                check=Q(amount__gt=0),
                name="bid_amount_gt_0",
            ),
        ]

    def clean(self) -> None:
        """Validate bid amount and auction status.
        
        Ensures:
        1. Auction hasn't ended
        2. Bid exceeds current highest bid or starting price
        
        Raises:
            ValidationError: If auction has ended or bid is not high enough
        """
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


class Follow(models.Model):
    """User follower relationship for social features.
    
    Allows users to follow sellers and receive notifications when they list new items.
    
    Attributes:
        follower: User who is following
        followee: User being followed
        created_at: Timestamp when follow relationship was created
    
    Constraints:
        - unique_follow: A user can only follow another user once
        - Users cannot follow themselves (validated in clean())
    """
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following",
        help_text="The user who is following"
    )
    followee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers",
        help_text="The user being followed"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'followee'],
                name='unique_follow'
            ),
        ]
        ordering = ['-created_at']

    def clean(self) -> None:
        """Prevent users from following themselves.
        
        Raises:
            ValidationError: If follower and followee are the same user
        """
        super().clean()
        
        # Prevent users from following themselves
        if self.follower_id == self.followee_id:
            raise ValidationError("Users cannot follow themselves.")

    def __str__(self) -> str:
        return f"{self.follower.username} follows {self.followee.username}"


class QuestionLike(models.Model):
    """Like/upvote for a user question.
    
    Tracks which users have liked specific questions.
    Users can only like each question once (unique constraint).
    
    Attributes:
        user: User who liked the question
        question: Question that was liked
        created_at: Timestamp when like was created
    
    Constraints:
        - unique_question_like: A user can only like each question once
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="question_likes"
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="likes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'question'],
                name='unique_question_like'
            ),
        ]
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.user.username} likes question {self.question.id}"


class AnswerLike(models.Model):
    """Like/upvote for a seller answer.
    
    Tracks which users have liked specific answers.
    Users can only like each answer once (unique constraint).
    
    Attributes:
        user: User who liked the answer
        answer: Answer that was liked
        created_at: Timestamp when like was created
    
    Constraints:
        - unique_answer_like: A user can only like each answer once
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="answer_likes"
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name="likes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'answer'],
                name='unique_answer_like'
            ),
        ]
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.user.username} likes answer {self.answer.id}"

