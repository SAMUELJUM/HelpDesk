from django.core.paginator import Paginator
from django.db.models import Q
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
from django.contrib.auth.decorators import  user_passes_test


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
    user = request.user

    if user.user_type == 'ADMIN':
        return redirect('admin_dashboard')
    elif user.user_type == 'TECH':
        return redirect('technician_dashboard')
    else:
        return redirect('user_dashboard')

@login_required
def admin_dashboard(request):
    return render(request, 'dashboards/admin_dashboard.html')

@login_required
def technician_dashboard(request):
    return render(request, 'dashboards/technician_dashboard.html')

@login_required
def user_dashboard(request):
    return render(request, 'dashboards/employee_dashboard.html')


@login_required
def role_based_redirect(request):
    user = request.user

    if user.role == 'Admin':
        return redirect('admin_dashboard')
    elif user.role == 'Technician':
        return redirect('technician_dashboard')
    elif user.role == 'Employee':
        return redirect('employee_dashboard')
    else:
        return redirect('dashboard')

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
    return render(request, 'users/user_list.html', {'users': users})


@login_required
def user_detail_view(request, pk):
    """User detail view (admin only)"""
    if request.user.user_type != ADMIN:
        messages.error(request, "Unauthorized access.")
        return redirect('employee_dashboard')

    user = get_object_or_404(User, pk=pk)
    return render(request, 'users/users_detail.html', {'user': user})


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


def landing():
    return redirect('landing')




@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_users(request):
    users = User.objects.all().order_by('id')
    return render(request, 'admin/manage_users.html', {'users': users})

@login_required
def my_tickets_view(request):
    tickets = Ticket.objects.filter(user=request.user).order_by('-created_at')

    # Search and filter
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    if search_query:
        tickets = tickets.filter(title__icontains=search_query)
    if status_filter:
        tickets = tickets.filter(status=status_filter)

    paginator = Paginator(tickets, 10)  # Show 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'tickets/my_tickets.html', {
        'tickets': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
    })

@login_required
def ticket_list(request):
    """List tickets based on user role with search & filter"""
    query = request.GET.get('q')
    status_filter = request.GET.get('status')
    tickets = Ticket.objects.all()

    if not (request.user.is_superuser or request.user.groups.filter(name='Admin').exists()):
        if request.user.groups.filter(name='Technician').exists():
            tickets = tickets.filter(assigned_to=request.user)
        else:
            tickets = tickets.filter(created_by=request.user)

    if query:
        tickets = tickets.filter(Q(title__icontains=query) | Q(description__icontains=query))

    if status_filter:
        tickets = tickets.filter(status=status_filter)

    paginator = Paginator(tickets.order_by('-created_at'), 10)
    page = request.GET.get('page')
    tickets_page = paginator.get_page(page)

    return render(request, 'tickets/ticket_list.html', {
        'tickets': tickets_page,
        'query': query,
        'status_filter': status_filter,
    })

from django.http import HttpResponseForbidden

def role_required(role):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.role != role:
                return HttpResponseForbidden("Access Denied")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Use like:
@login_required
@role_required('ADMIN')
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')


@login_required
@user_passes_test(lambda u: u.is_administrator)
def user_management(request):
    # Get all users
    users = User.objects.all().order_by('last_name', 'first_name')

    # Get role counts
    admin_count = User.objects.filter(role='ADMIN').count()
    tech_count = User.objects.filter(role='TECH').count()
    employee_count = User.objects.filter(role='USER').count()

    # Pagination
    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'users': page_obj,
        'admin_count': admin_count,
        'tech_count': tech_count,
        'employee_count': employee_count,
    }

    return render(request, 'users/user_management.html', context)
