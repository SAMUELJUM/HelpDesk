from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.utils import timezone
from helpdes.models import Ticket
from django.core.paginator import Paginator
from django.contrib import messages
from users.views import TECH, ADMIN
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404



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
    return render(request, 'dashboards:employee_dashboard.html')


@login_required
def dashboard(request):
    context = {}

    if request.user.is_superuser or request.user.is_staff:
        context.update({
            'high_priority_tickets': Ticket.objects.filter(priority='high').count(),
            'pending_tickets': Ticket.objects.filter(status='open').count(),
            'resolved_tickets': Ticket.objects.filter(status='resolved').count(),
            'recent_tickets': Ticket.objects.all()
                                  .order_by('-updated_at')[:5]
                                  .select_related('assigned_to')
        })
    else:
        context.update({
            'user_open_tickets': Ticket.objects.filter(created_by=request.user, status='open').count(),
            'user_in_progress_tickets': Ticket.objects.filter(created_by=request.user, status='in_progress').count(),
            'user_resolved_tickets': Ticket.objects.filter(created_by=request.user, status='resolved').count(),
            'my_recent_tickets': Ticket.objects.filter(created_by=request.user)
                                .order_by('-updated_at')[:5]
                                .prefetch_related('updates')
        })

    context['current_date'] = timezone.now().strftime("%B %d, %Y")

    return render(request, 'employee_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Admin-specific dashboard"""
    if request.user.user_type != ADMIN:
        messages.warning(request, "You don't have permission to access this page.")
        return redirect('employee_dashboard')

    return render(request, 'dashboards/admin_dashboard.html', {
        'title': 'Admin Dashboard',
        'user': request.user
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

