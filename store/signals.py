"""
Store signals for automatic watchlist management and email alerts
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import OrderItem, ProductWatchlist, Candy


@receiver(post_save, sender=OrderItem)
def add_ordered_product_to_watchlist(sender, instance, created, **kwargs):
    """
    Automatically add products to user's watchlist when they order them.
    Only adds if not already in watchlist.
    """
    if created and instance.order.user:
        ProductWatchlist.objects.get_or_create(
            user=instance.order.user,
            product=instance.product,
            defaults={"auto_added": True},
        )


@receiver(post_save, sender=Candy)
def check_and_send_low_stock_alerts(sender, instance, created, **kwargs):
    """
    Automatically send low stock alerts when product stock is updated.
    Checks all users watching this product and sends alerts if needed.
    """
    if created:
        return  # Don't send alerts for newly created products

    # Get all users watching this product
    watchers = ProductWatchlist.objects.filter(product=instance).select_related(
        "user", "user__preferences"
    )

    for watcher in watchers:
        # Check if user has low stock alerts enabled
        try:
            preferences = watcher.user.preferences
            if not preferences.low_stock_email_alerts:
                continue
        except Exception:
            continue

        # Determine threshold
        threshold = watcher.custom_threshold or preferences.low_stock_threshold

        # Check if stock is at or below threshold
        if instance.stock <= threshold:
            # Check if we've notified recently (within last 24 hours)
            if watcher.last_notified:
                time_since_last = timezone.now() - watcher.last_notified
                if time_since_last < timedelta(hours=24):
                    continue  # Skip if notified recently

            # Send email alert
            if watcher.user.email:
                send_low_stock_alert_email(
                    watcher.user, instance, instance.stock, threshold
                )

                # Update last_notified
                watcher.last_notified = timezone.now()
                watcher.save()


def send_low_stock_alert_email(user, product, stock, threshold):
    """Send low stock alert email to a single user"""
    subject = f"⚠️ Low Stock Alert: {product.name}"

    message = f"""
Hi {user.username},

An item on your watchlist is running low on stock:

  • {product.name} - Only {stock} left! (Your alert threshold: {threshold})

Order now before it's gone!

Visit Keanu's Candy Store: http://localhost:8000/candy/{product.id}/

---
To manage your watchlist and notification preferences, visit your account page.
"""

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
    except Exception as e:
        # Log error but don't crash
        print(f"Failed to send email to {user.email}: {e}")
