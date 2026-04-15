from django import forms

from .models import Dish


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = [
            "name",
            "description",
            "meal_slot",
            "main_ingredient_amount",
            "price",
            "quantity_available",
            "media",
            "is_published",
        ]
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Example: Main ingredient: chicken. Share what makes this dish special today.",
                }
            ),
            "main_ingredient_amount": forms.NumberInput(attrs={"min": "1", "step": "1"}),
            "price": forms.NumberInput(attrs={"min": "1", "step": "0.01"}),
            "quantity_available": forms.NumberInput(attrs={"min": "1"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update(
            {"placeholder": "Paneer Paratha"}
        )
        self.fields["meal_slot"].widget.attrs.update({"class": "role-select"})
        self.fields["main_ingredient_amount"].widget.attrs.update({"placeholder": "120"})
        self.fields["price"].widget.attrs.update({"placeholder": "120"})
        self.fields["quantity_available"].widget.attrs.update({"placeholder": "10"})
        self.fields["media"].required = False
        self.fields["main_ingredient_amount"].required = False
