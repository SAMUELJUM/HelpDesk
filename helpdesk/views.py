from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.utils import timezone
from tickets.models import Ticket, TicketCategory
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import HttpResponse
import csv
from helpdesk.duration_filters import get_default_duration,DurationFilter
#from .models import Ticket
#from users.views import TEMP, ADMIN, EMP
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django import forms


@login_required
def my_tickets_view(request):
    tickets = Ticket.objects.filter(created_by=request.user)

    search = request.GET.get('search')
    if search:
        tickets = tickets.filter(title__icontains=search)

    status = request.GET.get('status')
    if status:
        tickets = tickets.filter(status=status)

    paginator = Paginator(tickets.order_by('-updated_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'tickets': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'paginator': paginator,
        'search': search or '',
        'status': status or '',
    }
    return render(request, 'tickets:my_tickets.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # Redirect based on user_type
            if user.is_superuser or user.user_type == 'ADMIN':
                return redirect('admin_dashboard')
            elif user.user_type == 'TECH':
                return redirect('technician_dashboard')
            elif user.user_type == 'EMP':
                return redirect('employee_dashboard')
            else:
                return redirect('dashboard')  # fallback
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'registration/login.html')


@login_required
def dashboard_view(request):
    user = request.user
    context = {}

    # Admin Dashboard
    if getattr(user, 'role', '') == 'Admin' or user.is_superuser or user.is_staff:
        context.update({
            'high_priority_tickets': Ticket.objects.filter(priority='High').count(),
            'pending_tickets': Ticket.objects.filter(status='Open').count(),
            'resolved_tickets': Ticket.objects.filter(status='Resolved').count(),
            'recent_tickets': Ticket.objects.select_related('assigned_to')
                                            .order_by('-updated_at')[:5]
        })
        context['current_date'] = timezone.now().strftime("%B %d, %Y")
        return render(request, 'dashboards/admin_dashboard.html', context)

    # Technician Dashboard
    elif getattr(user, 'role', '') == 'Technician':
        context.update({
            'assigned_tickets': Ticket.objects.filter(assigned_to=user).count(),
            'in_progress_tickets': Ticket.objects.filter(assigned_to=user, status='In Progress').count(),
            'resolved_tickets': Ticket.objects.filter(assigned_to=user, status='Resolved').count(),
            'recent_assigned_tickets': Ticket.objects.filter(assigned_to=user)
                                                     .order_by('-updated_at')[:5]
        })
        context['current_date'] = timezone.now().strftime("%B %d, %Y")
        return render(request, 'dashboards/technician_dashboard.html', context)

    # Employee Dashboard
    elif getattr(user, 'role', '') == 'Employee':
        context.update({
            'user_open_tickets': Ticket.objects.filter(created_by=user, status='Open').count(),
            'user_in_progress_tickets': Ticket.objects.filter(created_by=user, status='In Progress').count(),
            'user_resolved_tickets': Ticket.objects.filter(created_by=user, status='Resolved').count(),
            'my_recent_tickets': Ticket.objects.filter(created_by=user)
                                               .order_by('-updated_at')[:5]
        })
        context['current_date'] = timezone.now().strftime("%B %d, %Y")
        return render(request, 'dashboards/employee_dashboard.html', context)

    # Unknown Role Fallback
    else:
        return redirect('login')
@login_required
def admin_dashboard(request):
    """Admin-specific dashboard"""
    if request.user.user_type != 'ADMIN':
        messages.warning(request, "You don't have permission to access this page.")
        return redirect('employee_dashboard')

    return render(request, 'dashboards/admin_dashboard.html', {
        'title': 'Admin Dashboard',
        'user': request.user
    })

@login_required
def technician_dashboard(request):
    """Technician-specific dashboard"""
    if request.user.user_type != 'TECH':
        messages.warning(request, "You don't have permission to access this page.")
        return redirect('employee_dashboard')

    return render(request, 'dashboards/technician_dashboard.html', {
        'title': 'Technician Dashboard',
        'user': request.user
    })


# Helper to check if user is staff (admin or technician)
def is_admin_or_technician(user):
    return user.is_authenticated and (user.is_staff or user.groups.filter(name__in=['Admin', 'Technician']).exists())

@login_required
@user_passes_test(is_admin_or_technician)
def ticket_list(request):
    tickets = Ticket.objects.all().order_by('-created_at')
    return render(request, 'tickets:ticket_list.html', {'tickets': tickets})


def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    return render(request, 'tickets/ticket_detail.html', {'ticket': ticket})


@login_required
def employee_dashboard(request):
    """Employee-specific dashboard"""
    return render(request, 'dashboards/employee_dashboard.html', {
        'title': 'Employee Dashboard',
        'user': request.user
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def manage_users_view(request):
    # Dummy logic – replace with real user management
    users = []  # You can load all users here
    return render(request, 'admin/manage_users.html', {'users': users})



# Check if user is admin
def is_admin(user):
    return user.is_superuser


# User Detail View
@login_required
@user_passes_test(is_admin)
def user_detail_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, 'users/user_detail.html', {'user': user})


# Form for updating user
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_superuser']
        widgets = {
            'is_staff': forms.CheckboxInput(),
            'is_superuser': forms.CheckboxInput(),
        }


# User Update View
@login_required
@user_passes_test(is_admin)
def user_update_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('helpdesk:manage_users')
    else:
        form = UserUpdateForm(instance=user)
    return render(request, 'users/user_update.html', {'form': form, 'user': user})


# views.py
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_redirect(request):
    user = request.user

    if user.role == 'admin':
        return redirect('admin_dashboard')
    elif user.role == 'technician':
        return redirect('technician_dashboard')
    elif user.role == 'employee':
        return redirect('employee_dashboard')
    else:
        # fallback in case role is undefined
        return redirect('login')

def export_reports_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tickets_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Ticket ID', 'Title', 'Status', 'Category', 'Assigned To', 'Created At', 'Resolved At'])

    for ticket in Ticket.objects.all():
        writer.writerow([
            ticket.id,
            ticket.title,
            ticket.status,
            ticket.category.name if ticket.category else 'Uncategorized',
            ticket.assigned_to.username if ticket.assigned_to else 'Unassigned',
            ticket.created_at.strftime('%Y-%m-%d %H:%M'),
            ticket.resolved_at.strftime('%Y-%m-%d %H:%M') if ticket.resolved_at else 'N/A',
        ])

    return response



def reporting_view(request):
    # Get duration filter from your custom utility
    duration_filter = DurationFilter.from_request(request)  # Adjust based on your actual implementation

    # Ticket status counts (optimized single query)
    status_counts = Ticket.objects.aggregate(
        total=Count('id'),
        resolved=Count('id', filter=Q(status="Resolved")),
        pending=Count('id', filter=Q(status="Pending")),
        overdue=Count('id', filter=Q(status="Overdue"))
    )

    # Recent tickets with select_related for performance
    recent_tickets = Ticket.objects.select_related(
        'submitted_by',
        'category'
    ).order_by('-created_at')[:10]

    # Monthly trend data using your duration filter
    monthly = (
        Ticket.objects
        .filter(created_at__range=duration_filter.date_range)  # Use your duration filter's date range
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    # Prepare month labels and counts
    months = [entry["month"].strftime("%b %Y") for entry in monthly]
    counts = [entry["count"] for entry in monthly]

    # Category-based data
    categories = (
        Ticket.objects
        .values("category__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    category_labels = [entry["category__name"] or "Uncategorized" for entry in categories]
    category_counts = [entry["count"] for entry in categories]

    context = {
        "total_tickets": status_counts['total'],
        "resolved_tickets": status_counts['resolved'],
        "pending_tickets": status_counts['pending'],
        "overdue_tickets": status_counts['overdue'],
        "recent_tickets": recent_tickets,
        "months": months,
        "counts": counts,
        "category_labels": category_labels,
        "category_counts": category_counts,
        "duration_filter": duration_filter,  # Pass filter to template if needed
    }

    return render(request, "dashboards/reporting.html", context)
