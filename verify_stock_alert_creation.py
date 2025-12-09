import os
import django
from django.conf import settings
from django.test import Client
from django.urls import reverse

# Setup Django Environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "candystore.settings")
django.setup()
settings.ALLOWED_HOSTS.append("testserver")

from django.contrib.auth import get_user_model
from store.models import Candy, StockAlert


def verify_stock_alert_creation():
    print("--- Starting StockAlert Creation Verification ---")
    User = get_user_model()

    # 1. Setup Data
    username = "alert_test_user"
    password = "password123"
    user, _ = User.objects.get_or_create(username=username)
    user.set_password(password)
    user.save()

    candy, _ = Candy.objects.get_or_create(name="OOS Candy", defaults={"price": 5.00})
    candy.stock = 0
    candy.save()

    # Ensure no existing alert
    StockAlert.objects.filter(user=user, product=candy).delete()

    # 2. Login
    c = Client()
    c.login(username=username, password=password)

    # 3. Simulate "Add to Watchlist" (POST)
    url = reverse("add_to_watchlist", args=[candy.id])
    print(f"POSTing to {url} for OOS candy...")
    c.post(url)

    # 4. Verify StockAlert
    alert_exists = StockAlert.objects.filter(user=user, product=candy).exists()

    if alert_exists:
        print("VERDICT: PASSED - StockAlert was created automatically.")
    else:
        print("VERDICT: FAILED - StockAlert was NOT created.")


if __name__ == "__main__":
    verify_stock_alert_creation()
