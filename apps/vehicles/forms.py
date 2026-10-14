from django import forms

from .models import Vehicle


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ["plate_display", "vehicle_type", "capacity"]
        widgets = {
            "plate_display": forms.TextInput(attrs={"placeholder": "e.g. DEMO-123XY"}),
            "vehicle_type": forms.TextInput(attrs={"placeholder": "e.g. Toyota Hiace bus"}),
            "capacity": forms.NumberInput(attrs={"min": 1, "step": 1}),
        }

    def clean_capacity(self):
        capacity = self.cleaned_data["capacity"]
        if capacity is None or capacity < 1:
            raise forms.ValidationError("Capacity must be at least 1.")
        return capacity
