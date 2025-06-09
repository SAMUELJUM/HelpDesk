from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django import forms
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .forms import UserRegistrationForm, UserProfileForm, ProfileForm
from .models import User, Ticket


# Constants for user types
ADMIN = 'ADMIN'
TECH = 'TECH'
EMP = 'EMP'

# ----------------------------
# Authentication Views
# ----------------------------

def register(request):
    """Handle user registration with role assignment"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Normalize and validate user_type input from form POST data
            user_type_input = request.POST.get('user_type', EMP)
            user_type_input = user_type_input.upper()

            if user_type_input not in [ADMIN, TECH, EMP]:
                user.user_type = EMP
            else:
                user.user_type = user_type_input

            user.save()
            messages.success(request, "Registration successful! Please log in.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {
        'form': form,
        'user_types': {'ADMIN': 'Admin', 'TECH': 'Technician', 'EMP': 'Employee'}
    })



def login_view(request):
    """Handle user login with role-based redirection"""
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Logging for debugging
            print(f"User {user.username} ({user.user_type}) logged in successfully")

            # Set session variable
            request.session['user_type'] = user.user_type

            return redirect('dashboard_redirect')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})


@require_POST
@csrf_protect
def logout_view(request):
    """Handle secure logout with session cleanup"""
    logout(request)
    request.session.flush()
    response = redirect('login')
    response.delete_cookie('sessionid')
    response.delete_cookie('csrftoken')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    messages.info(request, "You have been logged out.")
    return response

# ----------------------------
# Dashboard Views
# ----------------------------

@login_required
def dashboard_redirect(request):
    """Redirect users to their appropriate dashboard"""
    if not request.user.user_type:
        request.user.user_type = EMP
        request.user.save()

    user_type = request.user.user_type

    if user_type == ADMIN:
        return redirect('admin_dashboard')
    elif user_type == TECH:
        return redirect('technician_dashboard')
    else:
        return redirect('employee_dashboard')


@login_required
def admin_dashboard(request):
    total_tickets = Ticket.objects.count()
    open_tickets = Ticket.objects.filter(status='OPEN').count()
    in_progress_tickets = Ticket.objects.filter(status='IN_PROGRESS').count()
    resolved_tickets = Ticket.objects.filter(status='RESOLVED').count()
    tickets = Ticket.objects.select_related('created_by', 'assigned_to', 'category').all()

    # For technician assignment dropdown
    technicians = User.objects.filter(role='TECHNICIAN')

    from django.core.paginator import Paginator
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'dashboards/admin_dashboard.html', {
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'in_progress_tickets': in_progress_tickets,
        'resolved_tickets': resolved_tickets,
        'page_obj': page_obj,
        'technicians': technicians,
    })


@login_required
def technician_dashboard(request):
    """Technician-specific dashboard"""
    if request.user.user_type != TECH:
        messages.warning(request, "You don't have permission to access this page.")
        return redirect('employee_dashboard')

    return render(request, 'dashboards/technician_dashboard.html', {
        'title': 'Technician Dashboard',
        'user': request.user
    })


@login_required
def employee_dashboard(request):
    """Employee-specific dashboard"""
    return render(request, 'dashboards/employee_dashboard.html', {
        'title': 'Employee Dashboard',
        'user': request.user
    })


# ----------------------------
# Profile Management
# ----------------------------

@login_required
def profile(request):
    """User profile view and update"""
    user = request.user
    profile = getattr(user, 'profile', None)

    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        user_form = UserProfileForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    return render(request, 'users/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


@login_required
def change_password_view(request):
    """Handle password changes"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'users/change_password.html', {'form': form})


# ----------------------------
# User Management (Admin Only)
# ----------------------------

@login_required
def user_list_view(request):
    """List all users (admin only)"""
    if request.user.user_type != ADMIN:
        messages.error(request, "Unauthorized access.")
        return redirect('employee_dashboard')

    users = User.objects.all().order_by('date_joined')
    return render(request, 'users/list.html', {'users': users})


@login_required
def user_detail_view(request, pk):
    """User detail view (admin only)"""
    if request.user.user_type != ADMIN:
        messages.error(request, "Unauthorized access.")
        return redirect('employee_dashboard')

    user = get_object_or_404(User, pk=pk)
    return render(request, 'users/detail.html', {'user': user})


@login_required
def user_update_view(request, pk):
    """Update a user's info (admin only)"""
    if request.user.user_type != ADMIN:
        messages.error(request, "Unauthorized access.")
        return redirect('employee_dashboard')

    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User information updated successfully.")
            return redirect('user_detail', pk=pk)
    else:
        form = UserUpdateForm(instance=user)

    return render(request, 'users/update.html', {
        'form': form,
        'user_obj': user
    })


# ----------------------------
# Utility Classes
# ----------------------------

class UserUpdateForm(forms.ModelForm):
    """Form for updating user details"""

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'email': forms.EmailInput(attrs={'required': True}),
        }


def change_password():
    return None

def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    return render(request, 'helpdesk/ticket_detail.html', {'ticket': ticket})

