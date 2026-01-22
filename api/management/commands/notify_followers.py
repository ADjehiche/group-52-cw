"""Django management command to notify followers about new items from followed users.

This command should be run periodically (e.g., via cron job) to send email
notifications to users when someone they follow lists a new auction item.
It checks for items created within a configurable time window (default: 1 hour).

Usage:
    python manage.py notify_followers                # Last 1 hour (default)
    python manage.py notify_followers --hours 24     # Last 24 hours

Typical cron schedule: Every hour
    0 * * * * cd /path/to/project && python manage.py notify_followers
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import Follow, Item


class Command(BaseCommand):
    help = "Notify followers when users they follow list new items"

    def add_arguments(self, parser) -> None:
        """Define command-line arguments for this command.
        
        Args:
            parser: ArgumentParser instance to add arguments to
        """
        parser.add_argument(
            "--hours",
            type=int,
            default=1,
            help="Number of hours to look back for new items (default: 1)"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Main entry point for the management command.
        
        Finds all items created within the specified time window (--hours argument)
        and sends email notifications to followers of each item's owner.
        
        Args:
            *args: Positional command-line arguments (unused)
            **options: Keyword command-line arguments, including:
                - hours (int): Number of hours to look back for new items
        """
        hours = options["hours"]
        time_threshold = timezone.now() - timedelta(hours=hours)
        
        # Find items created within the time threshold
        new_items = Item.objects.filter(
            created_at__gte=time_threshold
        ).select_related("owner")
        
        if not new_items.exists():
            self.stdout.write(self.style.SUCCESS(f"No new items found in the last {hours} hour(s)."))
            return
        
        total_notifications = 0
        
        for item in new_items:
            # Get all followers of the item owner
            followers = Follow.objects.filter(followee=item.owner).select_related("follower")
            
            if not followers.exists():
                continue
            
            # Prepare email
            subject = f"New item from {item.owner.username} on Cbay!"
            message = f"""
Hello!

{item.owner.username} just listed a new item on Cbay that you might be interested in:

Item: {item.title}
Starting Price: £{item.starting_price}
Description: {item.description[:200]}{'...' if len(item.description) > 200 else ''}
Ends at: {item.ends_at.strftime('%Y-%m-%d %H:%M:%S')}

View the item here: {settings.SITE_URL}/items/{item.id}/

Happy bidding!
The Cbay Team
"""
            
            # Send email to each follower
            recipient_emails = [f.follower.email for f in followers if f.follower.email]
            
            if recipient_emails:
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        recipient_emails,
                        fail_silently=False,
                    )
                    total_notifications += len(recipient_emails)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Sent notification for item '{item.title}' to {len(recipient_emails)} follower(s)."
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Failed to send notifications for item '{item.title}': {str(e)}"
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Notification task complete. Sent {total_notifications} email(s) for {new_items.count()} new item(s)."
            )
        )
