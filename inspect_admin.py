import os
import django
from django.conf import settings

# Setup Django Environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "candystore.settings")
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import UserPreferences


def check_admin_status():
    print("--- Checking Admin User Status ---")
    User = get_user_model()

    try:
        admin_user = User.objects.get(username="admin")
        print(f"Admin User Found: {admin_user.username}")
        print(f"Email: '{admin_user.email}' (Is it empty?)")

        # Check Preferences
        try:
            prefs = admin_user.preferences
            print(f"Preferences Found:")
            print(f"  - Restock Alerts: {prefs.restock_email_alerts}")
            print(f"  - Low Stock Alerts: {prefs.low_stock_email_alerts}")
        except UserPreferences.DoesNotExist:
            print("ERROR: Admin user has NO preferences object created.")

    except User.DoesNotExist:
        print("ERROR: User 'admin' does not exist.")


if __name__ == "__main__":
    check_admin_status()
