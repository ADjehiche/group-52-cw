"""Django forms for user registration and authentication.

This module contains custom forms extending Django's built-in auth forms
to support the CBay auction application's user registration flow.
"""
from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class SignUpForm(UserCreationForm):
    """Custom user registration form extending Django's UserCreationForm.
    
    Adds email field as required and validates email uniqueness.
    Fields: username, email, password1 (Password), password2 (Password confirmation)
    
    Attributes:
        email: EmailField marked as required for user registration
    """
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self) -> str:
        """Validate and clean the email field.
        
        Ensures email is provided, normalized (lowercase), and unique in the database.
        
        Returns:
            str: The cleaned, lowercased email address
        
        Raises:
            forms.ValidationError: If email is empty or already exists in database
        """
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("Email is required.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email
