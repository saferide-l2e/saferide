"""Account details and consent for staff-reviewed booking eligibility."""

from django import forms


class VerificationDeclarationForm(forms.Form):
    profile_name = forms.CharField(
        label="Your full display name", required=False, max_length=80,
        help_text="The name you would like your SafeRide team to recognise.",
        widget=forms.TextInput(attrs={"autocomplete": "name", "placeholder": "e.g. Tolu Adewale"}),
    )
    home_area = forms.CharField(
        label="Area of Lagos", required=False, max_length=80,
        help_text="Your usual commuting area. Do not enter a street address.",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Yaba"}),
    )
    preferred_stop = forms.ChoiceField(
        label="Preferred boarding stop", required=False,
        choices=[("", "Select a stop"), ("Jibowu", "Jibowu"), ("Mile 2", "Mile 2"),
                 ("Yaba", "Yaba"), ("Oshodi", "Oshodi"), ("Ikeja", "Ikeja"),
                 ("Agege", "Agege"), ("Surulere", "Surulere"), ("CMS", "CMS"),
                 ("Maryland", "Maryland"), ("Berger", "Berger"),
                 ("Victoria Island", "Victoria Island"), ("Lekki Phase 1", "Lekki Phase 1")],
        help_text="Your preferred stop can be updated later.",
    )
    fictional_data = forms.BooleanField(
        label="I will provide only the account details requested.",
        help_text="Do not upload identity documents, licence numbers or other personal information.",
        error_messages={"required": "Confirm that you will provide only the requested account details."},
    )
    simulated_review = forms.BooleanField(
        label="I understand staff review is required for booking access.",
        help_text="Submitting a request does not approve your account or guarantee travel safety.",
        error_messages={"required": "Confirm that you understand the staff review requirement."},
    )
