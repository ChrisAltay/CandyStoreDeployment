"""
Store signals for automatic watchlist management and email alerts
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import OrderItem, ProductWatchlist, Candy, Order


@receiver(pre_save, sender=Order)
def track_order_status_change(sender, instance, **kwargs):
    """
    Track order status changes by storing old status on the instance.
    Runs before the order is saved.
    """
    if instance.pk:
        try:
            old_order = Order.objects.get(pk=instance.pk)
            instance._old_status = old_order.status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Order)
def send_order_status_emails(sender, instance, created, **kwargs):
    """
    Send emails when order status changes.
    """
    if not instance.user or not instance.user.email:
        return

    # 1. Order Confirmation (Created)
    if created:
        send_order_confirmation_email(instance)
        return

    # Check for status changes
    old_status = getattr(instance, "_old_status", None)
    new_status = instance.status

    if old_status != new_status:
        # 2. Shipping Notification
        if new_status == Order.STATUS_SHIPPED:
            send_shipping_email(instance)

        # 3. Delivery Notification
        elif new_status == Order.STATUS_DELIVERED:
            send_delivery_email(instance)

        # 4. Cancellation Notification
        elif new_status == Order.STATUS_CANCELLED:
            send_cancellation_email(instance)


def send_order_confirmation_email(order):
    """Send order confirmation email"""
    subject = f"Order Confirmation #{order.id}"
    message = f"""
Hi {order.user.username},

Thank you for your order!

Order #{order.id} has been received and is being processed.
Total: ${order.total_price}

We will notify you when it ships.

Visit Keanu's Candy Store: http://localhost:8000/orders/{order.id}/
"""
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send confirmation email: {e}")


def send_shipping_email(order):
    """Send shipping notification email"""
    subject = f"Order #{order.id} Shipped!"
    message = f"""
Hi {order.user.username},

Great news! Your order #{order.id} has been shipped.
It is on its way to you.

Track your order: http://localhost:8000/orders/{order.id}/
"""
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send shipping email: {e}")


def send_cancellation_email(order):
    """Send order cancellation email"""
    subject = f"Order #{order.id} Cancelled"
    message = f"""
Hi {order.user.username},

Your order #{order.id} has been successfully cancelled.

We have processed the cancellation and refunded any charges (if applicable) to your original payment method.
Stock for the items has been restored.

If you have any questions, please reply to this email.

Visit Keanu's Candy Store: http://localhost:8000/
"""
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send cancellation email: {e}")


def send_delivery_email(order):
    """Send order delivery email with special message"""
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags

    subject = f"Order #{order.id} Delivered! 🍬"

    # HTML Content
    html_content = f"""
    <html>
        <body>
            <h2>Hi {order.user.username},</h2>
            <p>Your order #{order.id} has arrived!</p>
            <p>Here is a digital candy for you as a thank you for ordering:</p>
            
            <div style="text-align: center; margin: 20px 0; font-size: 48px;">
                🍬🍬🍬<br>
                <img src="https://cdn-icons-png.flaticon.com/512/2682/2682458.png" alt="Digital Candy" style="width: 100px; height: 100px;">
                <br>🍬🍬🍬
            </div>

            <p style="font-weight: bold; color: #ff6b9d; font-size: 1.1em;">
                We appreciate Dr. Zimeng Lyu from Kean University for generously sponsoring these sweets!
            </p>

            <p>Enjoy your sweets!</p>
            <p><a href="http://localhost:8000/orders/{order.id}/">Visit Keanu's Candy Store</a></p>
        </body>
    </html>
    """

    text_content = strip_tags(html_content)

    try:
        msg = EmailMultiAlternatives(
            subject, text_content, settings.DEFAULT_FROM_EMAIL, [order.user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
    except Exception as e:
        print(f"Failed to send delivery email: {e}")


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
            if hasattr(watcher.user, "preferences"):
                preferences = watcher.user.preferences
                if not preferences.low_stock_email_alerts:
                    continue
                # Get threshold
                pref_threshold = preferences.low_stock_threshold
            else:
                # Default behavior if no prefs: Alerts ON, Threshold 3
                pref_threshold = 3
        except Exception as e:
            print(f"Pref Error: {str(e)}")
            continue

        # Determine threshold
        threshold = watcher.custom_threshold or pref_threshold

        # Check if stock is at or below threshold
        if instance.stock <= threshold:
            # Check if we've notified recently (within last 24 hours)
            # if watcher.last_notified:
            #     time_since_last = timezone.now() - watcher.last_notified
            #     if time_since_last < timedelta(hours=24):
            #         continue  # Skip if notified recently

            # Send email alert
            if watcher.user.email:
                send_low_stock_alert_email(
                    watcher.user, instance, instance.stock, threshold
                )

                # Update last_notified
                watcher.last_notified = timezone.now()
                watcher.save()
        else:
            pass


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
            fail_silently=False,
        )
    except Exception as e:
        # Log error but don't crash
        print(f"Failed to send email to {user.email}: {e}")


@receiver(post_save, sender=Candy)
def check_and_send_restock_alerts(sender, instance, created, **kwargs):
    """
    Automatically send restock alerts when product stock is updated.
    Checks for pending StockAlerts.
    """
    if created or instance.stock <= 0:
        return

    from .models import StockAlert

    # Get pending alerts for this product
    alerts = StockAlert.objects.filter(product=instance, notified=False).select_related(
        "user", "user__preferences"
    )

    for alert in alerts:
        # Check preferences
        try:
            preferences = alert.user.preferences
            if not preferences.restock_email_alerts:
                continue
        except Exception:
            continue

        if alert.user.email:
            send_restock_alert_email(alert.user, instance)

            # Mark as notified
            alert.notified = True
            alert.email_sent_at = timezone.now()
            alert.save()


def send_restock_alert_email(user, product):
    """Send restock alert email to a single user"""
    subject = f"✅ Back in Stock: {product.name}"

    message = f"""
Hi {user.username},

Good news! An item you requested is back in stock:

  • {product.name} - {product.stock} available now!

Order now before it sells out again!

Visit Keanu's Candy Store: http://localhost:8000/candy/{product.id}/

---
To manage your notifications, visit your account page.
"""

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send email to {user.email}: {e}")
