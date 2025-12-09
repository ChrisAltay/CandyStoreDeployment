import os
import django
from django.conf import settings

# Setup Django Environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "candystore.settings")
django.setup()

# Force locmem backend to capture emails in memory
settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

from django.core import mail
from django.contrib.auth import get_user_model
from store.models import Candy, StockAlert
from accounts.models import UserPreferences


def verify_restock_logic():
    print("--- Starting Restock Email Verification ---")

    # 1. Setup Test Data
    User = get_user_model()

    # Create a customer who is "offline" (just a user in the DB)
    customer_email = "offline_customer@example.com"
    customer, created = User.objects.get_or_create(
        username="offline_user", email=customer_email
    )
    if created:
        customer.set_password("password")
        customer.save()
        # Ensure they have preferences set to receive alerts
        UserPreferences.objects.get_or_create(
            user=customer, defaults={"restock_email_alerts": True}
        )
        print(f"Created test user: {customer.username}")
    else:
        # Reset prefs just in case
        if hasattr(customer, "preferences"):
            customer.preferences.restock_email_alerts = True
            customer.preferences.save()
        else:
            UserPreferences.objects.create(user=customer, restock_email_alerts=True)
        print(f"Using existing test user: {customer.username}")

    # Create a candy that is out of stock
    candy, _ = Candy.objects.get_or_create(name="Rare Candy", price=10.00, stock=0)
    candy.stock = 0  # Ensure it's 0
    candy.save()
    print(f"Created/Reset test candy: {candy.name} (Stock: {candy.stock})")

    # 2. Create a StockAlert (Simulate user clicking "Notify Me")
    # We delete any existing ones first to be clean
    StockAlert.objects.filter(user=customer, product=candy).delete()
    alert = StockAlert.objects.create(user=customer, product=candy, notified=False)
    print(f"Created StockAlert for {customer.username} watching {candy.name}")

    # 3. Trigger the Event (Simulate Admin updating stock)
    print(">>> ADMIN ACTION: Updating stock to 10...")

    # Clear outbox before action to ensure we catch NEW emails
    mail.outbox = []

    candy.stock = 10
    candy.save()  # This should trigger the post_save signal in store/signals.py

    # 4. Verification
    print("--- Verification Results ---")
    if len(mail.outbox) > 0:
        latest_email = mail.outbox[0]
        print(f"SUCCESS: Email found in outbox!")
        print(f"To: {latest_email.to}")
        print(f"Subject: {latest_email.subject}")
        print(f"Body Preview: {latest_email.body[:100]}...")

        if (
            customer_email in latest_email.to
            and "Back in Stock" in latest_email.subject
        ):
            print(
                "VERDICT: PASSED - The system correctly emailed the offline customer."
            )
        else:
            print("VERDICT: FAILED - Email sent but content/recipient incorrect.")
    else:
        print("VERDICT: FAILED - No email was sent.")
        print("Debugging info:")
        print(f"- User Prefs allow alerts? {customer.preferences.restock_email_alerts}")
        print(f"- Alert status: {StockAlert.objects.get(pk=alert.pk).notified}")

    # Cleanup
    # candy.delete()
    # customer.delete()


if __name__ == "__main__":
    verify_restock_logic()
