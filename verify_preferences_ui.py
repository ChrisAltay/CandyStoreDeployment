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
from accounts.models import UserPreferences


def verify_preferences_ui():
    print("--- Starting Preferences UI Verification ---")
    User = get_user_model()

    # 1. Get Test User
    username = "ui_test_user"
    password = "password123"
    email = "ui_test@example.com"

    user, created = User.objects.get_or_create(username=username, email=email)
    user.set_password(password)
    user.save()

    # Ensure prefs start FALSE
    prefs, _ = UserPreferences.objects.get_or_create(user=user)
    prefs.restock_email_alerts = False
    prefs.save()

    print(
        f"User {username} initial state: Restock Alerts = {prefs.restock_email_alerts}"
    )

    # 2. Simulate Login
    c = Client()
    login_success = c.login(username=username, password=password)
    if not login_success:
        print("ERROR: Login failed")
        return

    # 3. Simulate Checking the Box (POST with restock_email_alerts='on')
    # Note: HTML checkboxes modify state by being PRESENT (on) or ABSENT (off)
    url = reverse("update_preferences")
    print(f"POSTing to {url} with restock_email_alerts='on'...")

    response = c.post(
        url,
        {
            "restock_email_alerts": "on",
            # low_stock is optional/unchecked
        },
    )

    if response.status_code == 302:
        print("Success: Redirected (Post Successful)")
    else:
        print(f"Error: Status Code {response.status_code}")
        print(response.content)

    # 4. Verify Database
    prefs.refresh_from_db()
    print(f"User {username} NEW state: Restock Alerts = {prefs.restock_email_alerts}")

    if prefs.restock_email_alerts:
        print("VERDICT: PASSED - Preference was enabled.")
    else:
        print("VERDICT: FAILED - Preference remained False.")

    # 5. Simulate Unchecking (POST without the key)
    print("POSTing to {url} with empty form (unchecking)...")
    c.post(url, {})  # Empty dict simulates unchecked boxes

    prefs.refresh_from_db()
    print(f"User {username} FINAL state: Restock Alerts = {prefs.restock_email_alerts}")

    if not prefs.restock_email_alerts:
        print("VERDICT: PASSED - Preference was disabled.")
    else:
        print("VERDICT: FAILED - Preference remained True.")


if __name__ == "__main__":
    verify_preferences_ui()
