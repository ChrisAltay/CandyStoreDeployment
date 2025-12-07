from django import forms
from .models import Candy


class CandyForm(forms.ModelForm):
    class Meta:
        model = Candy
        fields = ["name", "description", "price", "stock", "category", "image_url"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }
