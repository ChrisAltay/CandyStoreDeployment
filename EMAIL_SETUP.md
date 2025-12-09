# Email Setup Instructions

## To Send Real Emails:

### Step 1: Get Gmail App Password
1. Go to your Google Account: https://myaccount.google.com/
2. Click "Security" in the left sidebar
3. Enable "2-Step Verification" if not already enabled
4. Search for "App passwords" or go to: https://myaccount.google.com/apppasswords
5. Create a new app password:
   - Select app: "Mail"
   - Select device: "Windows Computer" (or Other)
   - Click "Generate"
6. **Copy the 16-character password** (you won't see it again!)

### Step 2: Create .env File
1. Copy `.env.example` to `.env`:
   ```
   copy .env.example .env
   ```

2. Edit `.env` and fill in your credentials:
   ```
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-actual-email@gmail.com
   EMAIL_HOST_PASSWORD=your-16-char-app-password
   DEFAULT_FROM_EMAIL=noreply@keanuscandystore.com
   ```

### Step 3: Install python-dotenv
```bash
pip install python-dotenv
```

### Step 4: Update settings.py
Add this at the very top of `candystore/settings.py`:
```python
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
```

### Step 5: Restart Server
Stop and restart your Django server for changes to take effect.

### Step 6: Test
Place an order and watch for real emails to arrive!

---

## Security Notes:
- **NEVER commit `.env` to Git** - it contains your password!
- Add `.env` to your `.gitignore` file
- `.env.example` is safe to commit (no real credentials)

## Troubleshooting:
- **"Username and Password not accepted"**: Make sure you're using an App Password, not your regular Gmail password
- **"SMTPAuthenticationError"**: Double-check your email and app password
- **No email received**: Check spam folder, verify email address is correct
