import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "candystore.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = "admin"
password = "cps5301"
email = "admin@example.com"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser '{username}' created successfully.")
else:
    print(f"User '{username}' already exists. Updating to superuser.")
    u = User.objects.get(username=username)
    u.is_superuser = True
    u.is_staff = True
    u.set_password(password)
    u.save()
    print(f"User '{username}' updated to superuser with reset password.")
