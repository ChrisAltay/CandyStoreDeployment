from django import forms
from .models import Candy


class CandyForm(forms.ModelForm):
    class Meta:
        model = Candy
        fields = ["name", "description", "price", "stock", "category", "image_url"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=200, label="Full Name")
    address = forms.CharField(max_length=255, label="Address")
    city = forms.CharField(max_length=100, label="City")
    zip_code = forms.CharField(max_length=20, label="Zip Code")
    card_number = forms.CharField(
        max_length=19,
        label="Credit Card Number (Mock)",
        help_text="For testing, use any 16 digit number",
    )
    expiry = forms.CharField(
        max_length=5, label="Expiry (MM/YY)", initial="12/26"
    )
    cvv = forms.CharField(max_length=4, label="CVV")