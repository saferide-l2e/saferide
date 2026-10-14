from django import forms

from apps.routes.models import Route

from .models import IncidentCategory, RouteUpdateType


class ReviewForm(forms.Form):
    stars = forms.ChoiceField(
        choices=[(n, f"{n} star{'s' if n != 1 else ''}") for n in range(1, 6)],
        widget=forms.RadioSelect,
    )
    comment = forms.CharField(
        required=False, max_length=2000, widget=forms.Textarea(attrs={"rows": 3})
    )


class IncidentForm(forms.Form):
    category = forms.ChoiceField(choices=IncidentCategory.choices)
    description = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), max_length=4000)


class RouteUpdateForm(forms.Form):
    route = forms.ModelChoiceField(queryset=Route.objects.filter(is_active=True))
    type = forms.ChoiceField(choices=RouteUpdateType.choices)
    note = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), max_length=2000)
    occurred_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
