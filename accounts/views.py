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
            return render(request, "accounts/register.html")

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/register.html")

        # User existence check
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "accounts/register.html")

        # Create user
        user = User.objects.create_user(
            username=username, email=email, password=password
        )

        messages.success(request, "Account created! Please log in.")
        return redirect("login")

    return render(request, "accounts/register.html")


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
    """User account page with preferences and watchlist"""
    from store.models import Favorite, Review, ProductWatchlist
    from .models import UserPreferences
    from .forms import UserPreferencesForm, UserProfileForm

    favorites = Favorite.objects.filter(user=request.user).select_related("candy")
    reviews = Review.objects.filter(user=request.user).select_related("candy")

    preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    watchlist = ProductWatchlist.objects.filter(user=request.user).select_related(
        "product"
    )

    context = {
        "user": request.user,
        "favorites": favorites,
        "reviews": reviews,
        "preferences": preferences,
        "preferences_form": UserPreferencesForm(instance=preferences),
        "profile_form": UserProfileForm(instance=request.user),
        "watchlist": watchlist,
    }
    return render(request, "accounts/account.html", context)


@login_required
def update_preferences(request):
    """Update user notification preferences"""
    from .forms import UserPreferencesForm
    from .models import UserPreferences

    if request.method == "POST":
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        form = UserPreferencesForm(request.POST, instance=preferences)

        if form.is_valid():
            form.save()
            messages.success(request, "Notification preferences updated successfully!")
        else:
            print("Form errors:", form.errors)
            messages.error(request, "Error updating preferences. Please try again.")

    return redirect("account")


@login_required
def update_profile(request):
    """Update user profile information"""
    from .forms import UserProfileForm

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
        else:
            messages.error(request, "Error updating profile. Please check the form.")

    return redirect("account")


@login_required
def remove_from_watchlist(request, product_id):
    """Remove a product from user's watchlist"""
    from store.models import ProductWatchlist, Candy

    if request.method == "POST":
        try:
            watchlist_item = ProductWatchlist.objects.get(
                user=request.user, product_id=product_id
            )
            product_name = watchlist_item.product.name
            watchlist_item.delete()
            messages.success(request, f"Removed {product_name} from your watchlist.")
        except ProductWatchlist.DoesNotExist:
            messages.error(request, "Item not found in your watchlist.")

    return redirect("account")


@login_required
def update_watchlist_threshold(request, product_id):
    """Update the alert threshold for a specific watchlist item"""
    from store.models import ProductWatchlist

    if request.method == "POST":
        try:
            watchlist_item = ProductWatchlist.objects.get(
                user=request.user, product_id=product_id
            )
            threshold = request.POST.get("threshold")

            if threshold:
                threshold = int(threshold)
                # Validate threshold is positive
                if threshold > 0:
                    watchlist_item.custom_threshold = threshold
                    watchlist_item.save()
                    messages.success(
                        request,
                        f"Alert threshold for {watchlist_item.product.name} updated to {threshold}",
                    )
                else:
                    messages.error(request, "Threshold must be greater than 0")
            else:
                messages.error(request, "Please enter a valid threshold")

        except ProductWatchlist.DoesNotExist:
            messages.error(request, "Item not found in your watchlist.")
        except ValueError:
            messages.error(request, "Please enter a valid number")

    return redirect("account")
