from django.test import Client
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse

from django.conf import settings


def test_password_change_email():
    # 0. Allow testserver and setup email backend
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ["testserver"]
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    # 1. Setup User
    user, _ = User.objects.get_or_create(
        username="test_pw_user", email="testpw@example.com"
    )
    user.set_password("old_password")
    user.save()

    # 2. Login
    client = Client()
    login_success = client.login(username="test_pw_user", password="old_password")
    if not login_success:
        print("Error: Login failed")
        return

    # Clear outbox
    mail.outbox = []

    # 3. Execute Request
    # Note: PasswordChangeView usually requires 'old_password', 'new_password1', 'new_password2'
    response = client.post(
        reverse("password_change"),
        {
            "old_password": "old_password",
            "new_password1": "new_password123",
            "new_password2": "new_password123",
        },
        follow=True,
    )

    # 4. Verify Response
    if response.status_code == 200:
        # Check if we landed on success page or form error
        # If success, we should see "Password changed successfully" or similar, or be redirected
        if "password_change_done" in response.request[
            "PATH_INFO"
        ] or "successfully" in str(response.content):
            print("Success: Redirected/Completed")
        else:
            print("Warning: Might have stayed on same page (Form Invalid?)")
            # Print form errors if any
            if "form" in response.context:
                print(f"Form Errors: {response.context['form'].errors}")
    else:
        print(f"Error: Status Code {response.status_code}")

    # 5. Verify Email
    if len(mail.outbox) > 0:
        email = mail.outbox[0]
        print(f"Email Sent: {email.subject}")
        if "Password Changed Successfully" in email.subject:
            print("VERIFICATION PASSED: Correct email subject")
        else:
            print("VERIFICATION FAILED: Incorrect subject")
    else:
        print("VERIFICATION FAILED: No email sent")

    # Cleanup
    user.delete()


test_password_change_email()
