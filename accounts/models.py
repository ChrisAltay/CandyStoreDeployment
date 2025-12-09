"""
Accounts models
"""

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserPreferences(models.Model):
    """User notification preferences for inventory alerts"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="preferences"
    )
    low_stock_email_alerts = models.BooleanField(
        default=True, help_text="Email when watched items are running low"
    )
    restock_email_alerts = models.BooleanField(
        default=True, help_text="Email when out-of-stock items restock"
    )
    low_stock_threshold = models.IntegerField(
        default=3,
        help_text="Alert when stock is at or below this number",
    )

    class Meta:
        verbose_name_plural = "User preferences"

    def __str__(self):
        return f"{self.user.username}'s preferences"


@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """Automatically create preferences when a new user is created"""
    if created:
        UserPreferences.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_preferences(sender, instance, **kwargs):
    """Save preferences when user is saved"""
    if hasattr(instance, "preferences"):
        instance.preferences.save()
