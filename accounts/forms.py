from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm
from django.contrib.auth.models import User
from django.db import IntegrityError
from .models import Profile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=150, required=True)
    student_id = forms.CharField(max_length=50, required=False, help_text="Optional but recommended")

    class Meta:
        model = User
        fields = ('username', 'email', 'full_name', 'student_id', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter student ID (optional)'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('A user with this email address already exists. Please use a different email or try logging in.')
        return email

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if student_id:
            # Check if student_id already exists
            if Profile.objects.filter(student_id=student_id).exists():
                raise forms.ValidationError('A user with this student ID already exists. Please use a different student ID or leave it blank.')
        return student_id

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            try:
                user.save()
                # Only set student_id if it's not empty
                student_id = self.cleaned_data['student_id']
                if not student_id:
                    student_id = None
                Profile.objects.create(
                    user=user,
                    full_name=self.cleaned_data['full_name'],
                    student_id=student_id,
                    role='student'  # Always set to student for registration
                )
            except IntegrityError as e:
                # Handle any remaining integrity errors gracefully
                if 'email' in str(e).lower():
                    raise forms.ValidationError('A user with this email address already exists. Please use a different email or try logging in.')
                elif 'student_id' in str(e).lower():
                    raise forms.ValidationError('A user with this student ID already exists. Please use a different student ID or leave it blank.')
                else:
                    raise forms.ValidationError('An error occurred while creating your account. Please check your information and try again.')
        return user

class EmailAuthenticationForm(AuthenticationForm):
    """Custom authentication form that allows login with email or username"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email or Username'
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter email or username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check if it's an email format
            if '@' in username:
                matching_users = User.objects.filter(email=username)
                if not matching_users.exists():
                    # No user with this email; leave as-is so auth machinery can handle
                    return username
                if matching_users.count() > 1:
                    # If multiple users exist with the same email, 
                    # we need to handle this differently
                    # For now, we'll use the most recent active user
                    active_users = matching_users.filter(is_active=True).order_by('-date_joined')
                    if active_users.exists():
                        return active_users.first().username
                    else:
                        # If no active users, use the most recent one
                        return matching_users.order_by('-date_joined').first().username
                # Exactly one user found: map email to that username for auth
                return matching_users.first().username
        return username

class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )