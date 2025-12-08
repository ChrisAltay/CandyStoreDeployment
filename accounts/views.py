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
        email = request.POST.get("email")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        # Validation
        if not username or not password or not password2:
            messages.error(request, "All fields are required.")
            return render(request, "accounts/login.html", {"active_panel": "register"})

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/login.html", {"active_panel": "register"})

        # User existence check
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "accounts/login.html", {"active_panel": "register"})

        # Create user
        user = User.objects.create_user(
            username=username, email=email, password=password
        )

        messages.success(request, "Account created! Please log in.")
        return redirect("login")

    return render(request, "accounts/login.html", {"active_panel": "register"})


def login_view(request):
    if request.user.is_authenticated:
        logout(request)

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

    return render(request, "accounts/login.html", {"active_panel": "login"})


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
    from store.models import Favorite, Review  # Import here to avoid circular ref

    favorites = Favorite.objects.filter(user=request.user).select_related("candy")
    reviews = Review.objects.filter(user=request.user).select_related("candy")

    context = {
        "user": request.user,
        "favorites": favorites,
        "reviews": reviews,
    }
    return render(request, "accounts/account.html", context)
