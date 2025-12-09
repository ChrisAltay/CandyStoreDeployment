import os
import django
from django.conf import settings

# Setup Django Environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "candystore.settings")
django.setup()
settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

from django.core import mail
from django.contrib.auth import get_user_model
from store.models import Candy, Order, OrderItem, ProductWatchlist


def verify_distinct():
    print("--- Starting Distinct Email Verification ---")
    User = get_user_model()

    # Setup Data
    User.objects.filter(username__in=["u_watcher", "u_buyer", "u_hybrid"]).delete()
    candy = Candy.objects.create(name="Distinct Test Candy", price=10, stock=100)

    # 1. Watcher (Expect Watchlist Email)
    u_watcher = User.objects.create_user("u_watcher", "watch@e.com", "pass")
    ProductWatchlist.objects.create(user=u_watcher, product=candy, custom_threshold=10)
    # Ensure prefs enabled (default signal)
    u_watcher.preferences.low_stock_email_alerts = True
    u_watcher.preferences.save()

    # 2. Buyer (Expect History Email)
    u_buyer = User.objects.create_user("u_buyer", "buy@e.com", "pass")
    u_buyer.preferences.low_stock_email_alerts = True
    u_buyer.preferences.low_stock_threshold = 3
    u_buyer.preferences.save()
    Order.objects.create(user=u_buyer, total_price=10).items.create(
        product=candy, price=10, quantity=1
    )

    # 3. Hybrid (Expect Watchlist Email - Priority)
    u_hybrid = User.objects.create_user("u_hybrid", "hybrid@e.com", "pass")
    u_hybrid.preferences.low_stock_email_alerts = True
    u_hybrid.preferences.save()
    ProductWatchlist.objects.create(user=u_hybrid, product=candy, custom_threshold=10)
    Order.objects.create(user=u_hybrid, total_price=10).items.create(
        product=candy, price=10, quantity=1
    )

    print("Setup Complete. Triggering Alert (Stock -> 2)...")
    mail.outbox = []
    candy.stock = 2
    candy.save()

    emails = {m.to[0]: m for m in mail.outbox}

    # Check Watcher
    if "watch@e.com" in emails:
        body = emails["watch@e.com"].body
        if "An item on your watchlist is running low" in body:
            print("VERDICT Watcher: PASSED (Received Watchlist Template)")
        else:
            print(f"VERDICT Watcher: FAILED (Wrong Template: {body[:30]}...)")
    else:
        print("VERDICT Watcher: FAILED (No Email)")

    # Check Buyer
    if "buy@e.com" in emails:
        body = emails["buy@e.com"].body
        if "You previously purchased" in body:
            print("VERDICT Buyer:   PASSED (Received History Template)")
        else:
            print(f"VERDICT Buyer:   FAILED (Wrong Template: {body[:30]}...)")
    else:
        print("VERDICT Buyer:   FAILED (No Email)")

    # Check Hybrid
    if "hybrid@e.com" in emails:
        body = emails["hybrid@e.com"].body
        if "An item on your watchlist is running low" in body:
            print("VERDICT Hybrid:  PASSED (Received Watchlist Template - Priority)")
        else:
            print(f"VERDICT Hybrid:  FAILED (Wrong Template: {body[:30]}...)")
    else:
        print("VERDICT Hybrid:  FAILED (No Email)")

    # Cleanup
    candy.delete()
    u_watcher.delete()
    u_buyer.delete()
    u_hybrid.delete()


if __name__ == "__main__":
    verify_distinct()
