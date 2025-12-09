import os
import django
from django.conf import settings
from django.test import Client

# Setup Django Environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "candystore.settings")
django.setup()
settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

from django.core import mail
from django.contrib.auth import get_user_model
from store.models import Candy, Order, OrderItem
from accounts.models import UserPreferences


def verify_refactor():
    print("--- Starting Refactored Logic Verification ---")
    User = get_user_model()

    # Setup Data
    candy_restock = Candy.objects.create(name="Restock Candy", price=10, stock=0)
    candy_low = Candy.objects.create(name="Low Stock Candy", price=10, stock=100)

    # User 1: Global Restock ON, Low Stock ON, Bought 'Low Stock Candy'
    User.objects.filter(username__in=["user1", "user2", "user3"]).delete()
    user1 = User.objects.create_user("user1", "u1@e.com", "pass")
    pref1 = user1.preferences
    pref1.restock_email_alerts = True
    pref1.low_stock_email_alerts = True
    pref1.save()

    order1 = Order.objects.create(user=user1, total_price=10)
    OrderItem.objects.create(order=order1, product=candy_low, price=10, quantity=1)

    # User 2: Global Restock OFF, Low Stock ON, Bought 'Low Stock Candy'
    user2 = User.objects.create_user("user2", "u2@e.com", "pass")
    pref2 = user2.preferences
    pref2.restock_email_alerts = False
    pref2.low_stock_email_alerts = True
    pref2.save()

    order2 = Order.objects.create(user=user2, total_price=10)
    OrderItem.objects.create(order=order2, product=candy_low, price=10, quantity=1)

    # User 3: Global Restock ON, Low Stock ON, NEVER bought
    user3 = User.objects.create_user("user3", "u3@e.com", "pass")
    pref3 = user3.preferences
    pref3.restock_email_alerts = True
    pref3.low_stock_email_alerts = True
    pref3.save()

    print("Data Setup Complete.")

    # TEST 1: Global Restock
    print("\n>>> Testing Global Restock (Updating local stock)...")
    mail.outbox = []
    candy_restock.stock = 50
    candy_restock.save()

    print(f"Emails sent: {len(mail.outbox)}")
    recipients = [m.to[0] for m in mail.outbox]
    print(f"Recipients: {recipients}")

    # Expect: User 1 and User 3 (Restock=True). User 2 skipped.
    if (
        "u1@e.com" in recipients
        and "u3@e.com" in recipients
        and "u2@e.com" not in recipients
    ):
        print("VERDICT 1: PASSED (Global Restock)")
    else:
        print("VERDICT 1: FAILED")

    # TEST 2: Low Stock (Purchase History)
    print("\n>>> Testing Low Stock (Updating stock to 2)...")
    mail.outbox = []
    candy_low.stock = 2
    candy_low.save()

    print(f"Emails sent: {len(mail.outbox)}")
    recipients = [m.to[0] for m in mail.outbox]
    print(f"Recipients: {recipients}")

    # Expect: User 1 and User 2 (Bought it + LowStock=True). User 3 skipped (Never bought).
    if (
        "u1@e.com" in recipients
        and "u2@e.com" in recipients
        and "u3@e.com" not in recipients
    ):
        print("VERDICT 2: PASSED (Purchase History)")
    else:
        print("VERDICT 2: FAILED")

    # Cleanup
    User.objects.filter(username__in=["user1", "user2", "user3"]).delete()
    candy_restock.delete()
    candy_low.delete()


if __name__ == "__main__":
    verify_refactor()
