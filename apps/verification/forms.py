"""Fictional eligibility declaration for the staff-reviewed demo workflow."""

from django import forms


class VerificationDeclarationForm(forms.Form):
    fictional_data = forms.BooleanField(
        label="I am using a fictional demo profile.",
        help_text="Do not upload identity documents, licence numbers or other personal information.",
        error_messages={"required": "Confirm that you are using a fictional demo profile."},
    )
    simulated_review = forms.BooleanField(
        label="I understand this is a simulated review by SafeRide staff.",
        help_text="Submitting a request does not approve your account or guarantee travel safety.",
        error_messages={"required": "Confirm that you understand the simulated staff review."},
    )
