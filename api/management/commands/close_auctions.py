from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils import timezone

from api.models import Item, Bid


class Command(BaseCommand):
    help = "Close auctions that have ended and notify winners/owners"

    def handle(self, *args: Any, **options: Any) -> None:
        now = timezone.now()
        
        # Find ended items where notifications haven't been sent yet
        ended_items = Item.objects.filter(
            ends_at__lte=now,
            winner_notified=False
        ).select_related("owner")
        
        if not ended_items.exists():
            self.stdout.write(self.style.SUCCESS("No recently ended auctions found to process."))
            return
            
        processed_count = 0
        
        for item in ended_items:
            try:
                self.process_item(item)
                item.winner_notified = True
                item.save()
                processed_count += 1
                self.stdout.write(self.style.SUCCESS(f"Successfully closed auction for '{item.title}'"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing item '{item.title}': {e}"))
                
        self.stdout.write(self.style.SUCCESS(f"Processed {processed_count} auctions."))

    def process_item(self, item: Item) -> None:
        # Find highest bid
        highest_bid = item.bids.order_by("-amount").select_related("bidder").first()
        
        if highest_bid:
            winner = highest_bid.bidder
            amount = highest_bid.amount
            
            # 1. Notify Winner
            if winner.email:
                self.send_email(
                    subject=f"You won! {item.title}",
                    message=f"""
Congratulations {winner.username}!

You have won the auction for "{item.title}" with a bid of £{amount}.

Item Details:
- Title: {item.title}
- Final Price: £{amount}
- Seller: {item.owner.username}

You can view the item here: {settings.SITE_URL}/items/{item.id}/

Please contact the seller to arrange payment and delivery.

Best regards,
The Cbay Team
""",
                    recipient_list=[winner.email]
                )
            
            # 2. Notify Owner (Sold)
            if item.owner.email:
                self.send_email(
                    subject=f"Item Sold! {item.title}",
                    message=f"""
Great news {item.owner.username}!

Your item "{item.title}" has been sold to {winner.username} for £{amount}.

Buyer Details:
- Username: {winner.username}
- Email: {winner.email}

Please contact the buyer to arrange payment and delivery.

Best regards,
The Cbay Team
""",
                    recipient_list=[item.owner.email]
                )
        else:
            # 3. Notify Owner (Unsold)
            if item.owner.email:
                self.send_email(
                    subject=f"Auction Ended: {item.title}",
                    message=f"""
Hello {item.owner.username},

The auction for your item "{item.title}" has ended with no bids.

You can relist the item or create a new auction here: {settings.SITE_URL}/items/new/

Best regards,
The Cbay Team
""",
                    recipient_list=[item.owner.email]
                )

    def send_email(self, subject: str, message: str, recipient_list: list[str]) -> None:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
