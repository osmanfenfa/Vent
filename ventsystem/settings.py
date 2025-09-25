from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.urls import reverse
from .forms import UserRegistrationForm, EmailAuthenticationForm, PasswordResetForm, SetPasswordForm
from .models import Profile
from .token_generator import email_verification_token

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                username = form.cleaned_data.get('username')
                send_verification_email(request, user) # email verification 
                
                messages.success(request, f'Account created for {username}! Please check your email to verify your account before logging in.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'An error occurred while creating your account: {str(e)}') # unexpected errors handling during user creation
        else:
            # messages debugging error
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            try: # Check email verification
                profile = user.profile
                if not profile.email_verified:
                    messages.error(request, 'Please verify your email address before logging in. Check your email for the verification link.')
                    return render(request, 'accounts/login.html', {'form': form})
            except Profile.DoesNotExist:
                
                if user.is_superuser: # If no profile exists, check if superuser
                    Profile.objects.create(
                        user=user,
                        full_name=user.get_full_name() or user.username,
                        role='admin',
                        email_verified=True  # Superusers don't need email verification
                    )
                else:
                    Profile.objects.create(
                        user=user,
                        full_name=user.get_full_name() or user.username,
                        role='student',
                        email_verified=True  # For existing users, mark as verified
                    )

            login(request, user)   # Redirect based on user role
            try:
                profile = user.profile
                if profile.is_admin():
                    return redirect('admin_dashboard')
                else:
                    return redirect('student_dashboard')
            except Profile.DoesNotExist:
                return redirect('student_dashboard')
        else:
            # Handle authentication errors with more specific messages
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            
            if not username:
                messages.error(request, 'Please enter your email address or username.')
            elif not password:
                messages.error(request, 'Please enter your password.')
            else: # Check if user exists by username or email
                try:
                    user = User.objects.get(username=username) # First find by username
                    messages.error(request, 'Invalid password. Please check your password and try again.')
                except User.DoesNotExist:
                    try: # If not found by username, by email
                        user = User.objects.get(email=username)
                        messages.error(request, 'Invalid password. Please check your password and try again.')
                    except User.DoesNotExist:
                        messages.error(request, 'No account found with this email address or username. Please check your credentials or create a new account.')
    else:
        form = EmailAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

def send_verification_email(request, user):
    """Send email verification link to user"""
    token = email_verification_token.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    verification_url = request.build_absolute_uri(
        reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
    )
    
    subject = 'Verify Your Email Address - Vent'
    # Render HTML email template
    html_message = render_to_string('accounts/emails/email_verification.html', {
        'user': user,
        'verification_url': verification_url,
    })
    
    # Plain text fallback
    plain_message = f"""
    Hello {user.get_full_name() or user.username},
    
    Please click the link below to verify your email address:
    {verification_url}
    
    If you didn't create an account, please ignore this email.
    
    Best regards,
    Vent Team
    """
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )

def verify_email(request, uidb64, token):
    """Verify user's email address"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and email_verification_token.check_token(user, token):
        try:
            profile = user.profile
            profile.email_verified = True
            profile.save()
            messages.success(request, 'Your email has been verified successfully! You can now log in.')
        except Profile.DoesNotExist:
            messages.error(request, 'Profile not found.')
    else:
        messages.error(request, 'Invalid verification link.')
    
    return redirect('login')

def password_reset_request(request):
    """Handle password reset request"""
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            matching_users = User.objects.filter(email=email)
            if not matching_users.exists():
                messages.error(request, 'No account found with this email address.')
            elif matching_users.count() > 1:
                messages.error(
                    request,
                    'Multiple accounts are associated with this email. Please use your username to reset your password.'
                )
            else:
                send_password_reset_email(request, matching_users.first())
                messages.success(request, 'Password reset link has been sent to your email.')
                return redirect('login')
    else:
        form = PasswordResetForm()
    
    return render(request, 'accounts/password_reset.html', {'form': form})

def send_password_reset_email(request, user):
    """Send password reset link to user"""
    token = email_verification_token.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    reset_url = request.build_absolute_uri(
        reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    )
    
    subject = 'Password Reset Request - Vent'
    
    # Render HTML email template
    html_message = render_to_string('accounts/emails/password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
    })
    
    # Plain text fallback
    plain_message = f"""
    Hello {user.get_full_name() or user.username},
    
    You requested a password reset. Please click the link below to reset your password:
    {reset_url}
    
    If you didn't request this, please ignore this email.
    
    Best regards,
    Vent Team
    """
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )

def password_reset_confirm(request, uidb64, token):
    """Handle password reset confirmation"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and email_verification_token.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password has been reset successfully! You can now log in.')
                return redirect('login')
        else:
            form = SetPasswordForm(user)
        
        return render(request, 'accounts/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'Invalid password reset link.')
        return redirect('login')
