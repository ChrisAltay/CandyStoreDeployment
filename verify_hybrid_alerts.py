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
from store.models import Candy, Order, OrderItem, ProductWatchlist
from accounts.models import UserPreferences


def verify_hybrid():
    print("--- Starting Hybrid Logic Verification ---")
    User = get_user_model()

    # 1. Setup Data
    # Cleanup previous run
    User.objects.filter(username__in=["buyer", "watcher", "hybrid"]).delete()

    # Create Candy
    candy = Candy.objects.create(name="Hybrid Test Candy", price=10, stock=100)

    # User A: Buyer Only (Pref Default = 3)
    user_buyer = User.objects.create_user("buyer", "buyer@e.com", "pass")
    pref_b = user_buyer.preferences
    pref_b.low_stock_email_alerts = True
    pref_b.low_stock_threshold = 3
    pref_b.save()

    # Simulate Purchase
    order = Order.objects.create(user=user_buyer, total_price=10)
    OrderItem.objects.create(order=order, product=candy, price=10, quantity=1)

    # User B: Watcher Only (Custom Threshold = 10)
    user_watcher = User.objects.create_user("watcher", "watcher@e.com", "pass")
    pref_w = user_watcher.preferences  # defaults created by signal
    pref_w.low_stock_email_alerts = True  # ensure enabled globally
    pref_w.save()

    ProductWatchlist.objects.create(
        user=user_watcher, product=candy, custom_threshold=10
    )

    # User C: Hybrid (Buyer + Watcher with Custom Threshold = 5)
    user_hybrid = User.objects.create_user("hybrid", "hybrid@e.com", "pass")
    pref_h = user_hybrid.preferences
    pref_h.low_stock_email_alerts = True
    pref_h.low_stock_threshold = (
        3  # Default logic would ignore 5, but Watchlist should override
    )
    pref_h.save()

    Order.objects.create(user=user_hybrid, total_price=10).items.create(
        product=candy, price=10, quantity=1
    )
    ProductWatchlist.objects.create(user=user_hybrid, product=candy, custom_threshold=5)

    print("Setup Complete.")

    # TEST 1: Stock drops to 8
    # Expect: Watcher (Threshold 10) gets email. Buyer (3) & Hybrid (5) do NOT.
    print("\n>>> Stock -> 8")
    mail.outbox = []
    candy.stock = 8
    candy.save()

    recipients = [m.to[0] for m in mail.outbox]
    print(f"Recipients: {recipients}")

    if (
        "watcher@e.com" in recipients
        and "buyer@e.com" not in recipients
        and "hybrid@e.com" not in recipients
    ):
        print("VERDICT 1: PASSED")
    else:
        print("VERDICT 1: FAILED")

    # TEST 2: Stock drops to 4
    # Expect: Watcher (10) & Hybrid (5) get emails. Buyer (3) does NOT.
    print("\n>>> Stock -> 4")
    mail.outbox = []
    candy.stock = 4
    candy.save()

    recipients = [m.to[0] for m in mail.outbox]
    print(f"Recipients: {recipients}")

    if "hybrid@e.com" in recipients and "buyer@e.com" not in recipients:
        print("VERDICT 2: PASSED")
    else:
        print("VERDICT 2: FAILED")

    # TEST 3: Stock drops to 2
    # Expect: ALL get emails.
    print("\n>>> Stock -> 2")
    mail.outbox = []
    candy.stock = 2
    candy.save()

    recipients = [m.to[0] for m in mail.outbox]
    print(f"Recipients: {recipients}")

    if (
        "buyer@e.com" in recipients
        and "watcher@e.com" in recipients
        and "hybrid@e.com" in recipients
    ):
        print("VERDICT 3: PASSED (All notified)")
    else:
        print("VERDICT 3: FAILED")

    # Cleanup
    candy.delete()
    user_buyer.delete()
    user_watcher.delete()
    user_hybrid.delete()


if __name__ == "__main__":
    verify_hybrid()
