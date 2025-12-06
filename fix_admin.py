import os
import django
from django.test import Client

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "candystore.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

try:
    admin_user = User.objects.get(username="admin")
    print(f"Found user: {admin_user.username}")
    admin_user.set_password("cps5301")
    admin_user.save()
    print("Password reset to 'cps5301' successfully.")

    # Verify login
    from django.conf import settings

    settings.ALLOWED_HOSTS += ["testserver"]

    client = Client()
    login_successful = client.login(username="admin", password="cps5301")
    print(f"Client login successful: {login_successful}")

    if login_successful:
        response = client.get("/admin/")
        print(f"Access to /admin/ status code: {response.status_code}")
        if response.status_code == 200:
            print("Admin login verified successfully!")
        else:
            print("Login successful but failed to access /admin/")
    else:
        print("Failed to log in with new password.")

except User.DoesNotExist:
    print("User 'admin' does not exist.")
except Exception as e:
    print(f"An error occurred: {e}")
