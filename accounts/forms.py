"""
Accounts forms
"""

from django import forms
from .models import UserPreferences


class UserPreferencesForm(forms.ModelForm):
    """Form for updating user notification preferences"""

    class Meta:
        model = UserPreferences
        fields = [
            "low_stock_email_alerts",
            "restock_email_alerts",
        ]
        widgets = {
            "low_stock_email_alerts": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "restock_email_alerts": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "low_stock_threshold": forms.NumberInput(
                attrs={"class": "form-control", "min": "1", "max": "10"}
            ),
        }
        labels = {
            "low_stock_email_alerts": "Email me when items I've ordered are running low",
            "restock_email_alerts": "Email me when out-of-stock items I requested are back",
            "low_stock_threshold": "Alert me when stock is at or below",
        }
