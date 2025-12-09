from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_POST

User = get_user_model()


@staff_member_required
def admin_dashboard(request):
    """Main dashboard for admin capabilities"""
    return render(request, "accounts/admin_dashboard.html")


@staff_member_required
def user_list(request):
    """List all users for management"""
    users = User.objects.all().order_by("-date_joined")
    return render(request, "accounts/user_list.html", {"users": users})


@staff_member_required
@require_POST
def user_delete(request, pk):
    """Delete a user account"""
    user_to_delete = get_object_or_404(User, pk=pk)

    # Prevent self-deletion
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own account!")
        return redirect("user_list")

    username = user_to_delete.username
    user_to_delete.delete()
    messages.success(request, f"User '{username}' has been deleted successfully.")
    return redirect("user_list")
