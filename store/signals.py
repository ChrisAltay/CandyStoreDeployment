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


# @receiver(post_save, sender=OrderItem)
# def add_ordered_product_to_watchlist(sender, instance, created, **kwargs):
#     """
#     Automatically add products to user's watchlist when they order them.
#     Only adds if not already in watchlist.
#     """
#     if created and instance.order.user:
#         ProductWatchlist.objects.get_or_create(
#             user=instance.order.user,
#             product=instance.product,
#             defaults={"auto_added": True},
#         )


@receiver(post_save, sender=Candy)
def check_and_send_low_stock_alerts(sender, instance, created, **kwargs):
    """
    Automatically send low stock alerts when product stock is updated.
    Checks:
    1. Users who have PURCHASED this product (Default threshold).
    2. Users who are WATCHING this product (Custom threshold).
    """
    if created:
        return

    from django.contrib.auth import get_user_model
    from .models import ProductWatchlist

    User = get_user_model()

    # Track who to notify and WHY (Watcher vs Buyer)
    # targets[user_id] = {
    #    'user': user_obj,
    #    'threshold': int,
    #    'type': 'watchlist' | 'history'
    # }
    targets = {}

    # 1. Check Purchase History (Base layer)
    # Users who bought -> 'history' type
    past_buyers = (
        User.objects.filter(
            order__items__product=instance, preferences__low_stock_email_alerts=True
        )
        .distinct()
        .select_related("preferences")
    )

    for user in past_buyers:
        threshold = user.preferences.low_stock_threshold or 3
        # Pre-populate as history
        targets[user.id] = {"user": user, "threshold": threshold, "type": "history"}

    # 2. Check Watchlist (Overrides History)
    watchers = ProductWatchlist.objects.filter(product=instance).select_related(
        "user", "user__preferences"
    )

    for item in watchers:
        user = item.user

        # Determine base preference threshold
        if hasattr(user, "preferences"):
            pref_threshold = user.preferences.low_stock_threshold or 3
        else:
            pref_threshold = 3

        # Watchlist logic uses custom threshold if set
        final_threshold = (
            item.custom_threshold
            if item.custom_threshold is not None
            else pref_threshold
        )

        # Overwrite/Set as 'watchlist' type (Priority)
        targets[user.id] = {
            "user": user,
            "threshold": final_threshold,
            "type": "watchlist",
        }

    # 3. Process Notifications
    for user_id, data in targets.items():
        user = data["user"]
        threshold = data["threshold"]
        alert_type = data["type"]

        if instance.stock <= threshold:
            if user.email:
                if alert_type == "watchlist":
                    send_watchlist_low_stock_email(
                        user, instance, instance.stock, threshold
                    )
                else:
                    send_history_low_stock_email(
                        user, instance, instance.stock, threshold
                    )


def send_watchlist_low_stock_email(user, product, stock, threshold):
    """Send Watchlist specific low stock alert"""
    subject = f"⚠️ Watchlist Alert: {product.name} Low Stock"

    message = f"""
Hi {user.username},

An item on your watchlist is running low on stock:

  • {product.name} - Only {stock} left! (Your alert threshold: {threshold})

Order now before it's gone!

Visit Keanu's Candy Store: http://localhost:8000/candy/{product.id}/

---
To manage your watchlist, visit your account page.
"""
    _send_email_safe(user, subject, message)


def send_history_low_stock_email(user, product, stock, threshold):
    """Send Purchase History specific low stock alert"""
    subject = f"⚠️ Low Stock Alert: {product.name}"

    message = f"""
Hi {user.username},

You previously purchased {product.name}, and it is running low on stock!

Only {stock} left!

Order now before it's gone!

Visit Keanu's Candy Store: http://localhost:8000/candy/{product.id}/

---
To unsubscribe from these alerts, update your preferences in My Account.
"""
    _send_email_safe(user, subject, message)


def _send_email_safe(user, subject, message):
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


@receiver(pre_save, sender=Candy)
def track_candy_stock_change(sender, instance, **kwargs):
    """
    Track stock changes to determine if restock/low-stock events occurred.
    """
    if instance.pk:
        try:
            old_candy = Candy.objects.get(pk=instance.pk)
            instance._old_stock = old_candy.stock
        except Candy.DoesNotExist:
            instance._old_stock = None
    else:
        instance._old_stock = None


@receiver(post_save, sender=Candy)
def check_and_send_restock_alerts(sender, instance, created, **kwargs):
    """
    Automatically send restock alerts when product stock is updated.
    Sends to ALL users who have 'restock_email_alerts' enabled.
    Only sends if stock went from 0 to > 0.
    """
    if created:
        return

    # Check previous stock
    old_stock = getattr(instance, "_old_stock", None)

    # Only fire if it was OOS and now has stock
    if old_stock is not None and old_stock <= 0 and instance.stock > 0:
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Find ALL users who want restock alerts
        subscribers = User.objects.filter(preferences__restock_email_alerts=True)

        for user in subscribers:
            if user.email:
                send_restock_alert_email(user, instance)


def send_restock_alert_email(user, product):
    """Send restock alert email to a single user"""
    subject = f"✅ Back in Stock: {product.name}"

    message = f"""
Hi {user.username},

A candy is back in stock!

  • {product.name} - {product.stock} available now!

Order now: http://localhost:8000/candy/{product.id}/

---
To unsubscribe from restock alerts, visit your account page.
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
