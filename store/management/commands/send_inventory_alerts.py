"""
Management command to send inventory alert emails
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from store.models import ProductWatchlist, StockAlert
from accounts.models import UserPreferences


class Command(BaseCommand):
    help = "Send inventory alert emails for low stock and restocked items"

    def handle(self, *args, **kwargs):
        self.stdout.write("Checking inventory and sending alerts...")

        low_stock_count = self.send_low_stock_alerts()
        restock_count = self.send_restock_alerts()

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Sent {low_stock_count} low stock alerts and {restock_count} restock alerts"
            )
        )

    def send_low_stock_alerts(self):
        """Send alerts for items in watchlist that are low on stock"""
        sent_count = 0

        # Get all watchlist items
        watchlist_items = ProductWatchlist.objects.select_related(
            "user", "product", "user__preferences"
        ).all()

        # Group by user to send one email per user
        user_alerts = {}

        for item in watchlist_items:
            # Check if user has low stock alerts enabled
            try:
                preferences = item.user.preferences
                if not preferences.low_stock_email_alerts:
                    continue
            except UserPreferences.DoesNotExist:
                continue

            # Determine threshold (custom or global)
            threshold = item.custom_threshold or preferences.low_stock_threshold

            # Check if stock is at or below threshold
            if item.product.stock <= threshold:
                # Check if we've notified recently (within last 24 hours)
                if item.last_notified:
                    time_since_last = timezone.now() - item.last_notified
                    if time_since_last < timedelta(hours=24):
                        continue  # Skip if notified recently

                # Add to user's alert list
                if item.user.email:
                    if item.user not in user_alerts:
                        user_alerts[item.user] = []
                    user_alerts[item.user].append(
                        {
                            "product": item.product,
                            "stock": item.product.stock,
                            "threshold": threshold,
                        }
                    )

                    # Update last_notified
                    item.last_notified = timezone.now()
                    item.save()

        # Send emails
        for user, alerts in user_alerts.items():
            self.send_low_stock_email(user, alerts)
            sent_count += 1

        return sent_count

    def send_low_stock_email(self, user, alerts):
        """Send low stock alert email to user"""
        subject = "⚠️ Low Stock Alert - Items You're Watching"

        # Build email body
        product_list = "\n".join(
            [
                f"  • {alert['product'].name} - Only {alert['stock']} left! (Alert threshold: {alert['threshold']})"
                for alert in alerts
            ]
        )

        message = f"""
Hi {user.username},

Some items on your watchlist are running low on stock:

{product_list}

Order now before they're gone!

Visit Keanu's Candy Store: http://localhost:8000/

---
To manage your watchlist and notification preferences, visit your account page.
"""

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        self.stdout.write(f"  📧 Sent low stock alert to {user.email}")

    def send_restock_alerts(self):
        """Send alerts for items that have been restocked"""
        sent_count = 0

        # Get all stock alerts for items that are now in stock and haven't been notified
        alerts = StockAlert.objects.filter(
            notified=False, product__stock__gt=0
        ).select_related("user", "product", "user__preferences")

        # Group by user
        user_alerts = {}

        for alert in alerts:
            # Check if user has restock alerts enabled
            try:
                preferences = alert.user.preferences
                if not preferences.restock_email_alerts:
                    continue
            except UserPreferences.DoesNotExist:
                continue

            if alert.user.email:
                if alert.user not in user_alerts:
                    user_alerts[alert.user] = []
                user_alerts[alert.user].append(alert)

        # Send emails
        for user, user_alert_list in user_alerts.items():
            self.send_restock_email(user, user_alert_list)
            sent_count += len(user_alert_list)

            # Mark as notified
            for alert in user_alert_list:
                alert.notified = True
                alert.email_sent_at = timezone.now()
                alert.save()

        return sent_count

    def send_restock_email(self, user, alerts):
        """Send restock notification email to user"""
        if len(alerts) == 1:
            subject = f"✅ Back in Stock: {alerts[0].product.name}"
        else:
            subject = f"✅ {len(alerts)} Items Back in Stock!"

        # Build email body
        product_list = "\n".join(
            [
                f"  • {alert.product.name} - {alert.product.stock} in stock"
                for alert in alerts
            ]
        )

        message = f"""
Hi {user.username},

Good news! Items you requested are back in stock:

{product_list}

Order now before they sell out again!

Visit Keanu's Candy Store: http://localhost:8000/

---
To manage your notifications, visit your account page.
"""

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        self.stdout.write(f"  📧 Sent restock alert to {user.email}")
