import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "candystore.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print(f"User model: {User}")
users = User.objects.all()
print(f"Total users: {users.count()}")

for user in users:
    print(
        f"Username: {user.username}, Email: {user.email}, Is Staff: {user.is_staff}, Is Superuser: {user.is_superuser}, Active: {user.is_active}"
    )
