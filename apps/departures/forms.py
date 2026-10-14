from django import forms
from django.utils import timezone

from apps.routes.models import Route
from apps.vehicles.models import Vehicle


class DepartureForm(forms.Form):
    route = forms.ModelChoiceField(queryset=Route.objects.none())
    vehicle = forms.ModelChoiceField(queryset=Vehicle.objects.none())
    scheduled_departure_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        help_text="UTC. Must be at least 10 minutes ahead so a seat hold can be honoured.",
    )

    def __init__(self, *args, driver=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["route"].queryset = Route.objects.filter(is_active=True)
        if driver is not None:
            self.fields["vehicle"].queryset = Vehicle.objects.filter(
                driver__user=driver, approval_status="APPROVED"
            )

    def clean_scheduled_departure_at(self):
        value = self.cleaned_data["scheduled_departure_at"]
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())
        return value
