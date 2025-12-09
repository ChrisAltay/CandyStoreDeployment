"""
URLs for accounts app
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("account/", views.account_page, name="account"),
    path(
        "account/preferences/update/",
        views.update_preferences,
        name="update_preferences",
    ),
    path(
        "account/watchlist/remove/<int:product_id>/",
        views.remove_from_watchlist,
        name="remove_from_watchlist",
    ),
    path(
        "account/watchlist/threshold/<int:product_id>/",
        views.update_watchlist_threshold,
        name="update_watchlist_threshold",
    ),
    path("account/profile/update/", views.update_profile, name="update_profile"),
    path(
        "account/password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change_form.html",
            success_url="/accounts/account/password-change/done/",
        ),
        name="password_change",
    ),
    path(
        "account/password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html"
        ),
        name="password_change_done",
    ),
    # Password Reset URLs
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
