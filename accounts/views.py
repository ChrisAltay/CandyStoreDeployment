"""
Account views for user authentication
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages

User = get_user_model()


def register(request):  # Register new user
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        # Validation
        if not username or not password or not password2:
            messages.error(request, "All fields are required.")
            return render(request, "accounts/register.html")

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/register.html")

        # User existence check
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "accounts/register.html")

        # Create user
        user = User.objects.create_user(username=username, password=password)

        messages.success(request, "Account created! Please log in.")
        return redirect("login")

    return render(request, "accounts/register.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            next_url = request.POST.get("next") or request.GET.get("next", "/")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html")


def logout_view(request):
    """Custom logout view"""
    # Store logout message before clearing session
    messages.success(request, "You have been successfully logged out.")

    # Logout user (this clears auth-related session data)
    logout(request)

    return redirect("login")


@login_required
def account_page(request):
    """User account page"""
    context = {
        "user": request.user,
    }
    return render(request, "accounts/account.html", context)
