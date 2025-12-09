# Password Reset Email Debugging Guide

## Issue
Password reset emails are not being sent, but order confirmation emails work fine.

## Fixed
✅ Fixed template syntax error in `password_reset_email.html` (line 7: `{{ protocol}}` → `{{ protocol }}`)

## Things to Check

### 1. Check Server Console
When you submit the password reset form, check your terminal/console for:
- Any error messages
- Email sending confirmation
- Template rendering errors

### 2. Verify Email Exists in Database
**Important:** Django will NOT send a password reset email if the email address doesn't exist in the database. This is a security feature to prevent user enumeration.

To test:
1. Go to http://localhost:8000/accounts/password-reset/
2. Enter an email that you KNOW is registered in your database
3. Check the console for output

### 3. Check Email in Database
Run this command to see all user emails:
```bash
python manage.py shell
```
Then:
```python
from django.contrib.auth.models import User
for user in User.objects.all():
    print(f"Username: {user.username}, Email: {user.email}")
```

### 4. Test Email Sending Directly
In Django shell:
```python
from django.core.mail import send_mail
send_mail(
    'Test Subject',
    'Test message',
    'keanucandystore@gmail.com',
    ['your-test-email@example.com'],
    fail_silently=False,
)
```

### 5. Check .env File
Make sure your `.env` file has:
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=keanucandystore@gmail.com
EMAIL_HOST_PASSWORD=szsctfdldprcvpuj
DEFAULT_FROM_EMAIL=keanucandystore@gmail.com
```

### 6. Restart Server
After fixing the template, restart your Django server:
```bash
# Stop server (Ctrl+C)
python manage.py runserver
```

## Common Issues

### Email Not in Database
- **Symptom**: Form submits successfully, shows "Check your email" page, but no email arrives
- **Cause**: The email you entered doesn't match any user in the database
- **Solution**: Use an email that's actually registered, or register a new account with that email first

### Template Error
- **Symptom**: Error 500 or template rendering error in console
- **Cause**: Syntax error in email template (FIXED)
- **Solution**: Already fixed the `{{ protocol}}` typo

### Email Settings Wrong
- **Symptom**: Error in console about SMTP authentication
- **Cause**: Wrong email credentials
- **Solution**: Verify `.env` file has correct app password

## Next Steps
1. Restart your Django server
2. Try password reset with a registered email
3. Check console output
4. Let me know what you see!
