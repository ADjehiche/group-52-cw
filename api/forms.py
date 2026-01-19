from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class SignUpForm(UserCreationForm):
    # optional fields
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    profile_image = forms.ImageField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "date_of_birth", "profile_image", "password1", "password2")

    def clean_email(self) -> str:
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("Email is required.")
        # prevent duplicate emails
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email
