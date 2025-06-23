from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, Case, When, F, DurationField
from django.http import JsonResponse
from helpdesk.duration_filters import DurationFilter
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from .models import TicketCategory
#from .forms import TicketCategoryForm
import csv
from django.views.generic import TemplateView
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.contrib.auth import get_user_model, authenticate, login
from tickets.models import Ticket, Category
from tickets.forms import TicketFilterForm, TicketCategoryForm

User = get_user_model()

@login_required
def dashboard(request):
    context = {}
    tickets = Ticket.objects.none()

    if request.user.is_superuser or request.user.is_admin:
        tickets = Ticket.objects.all().order_by('-created_at')
    elif hasattr(request.user, 'is_technician') and request.user.is_technician:
        tickets = Ticket.objects.filter(
            Q(assigned_to=request.user) | Q(status='OPEN')
        ).order_by('-created_at')
    elif request.user.is_staff:
        tickets = Ticket.objects.all().order_by('-created_at')
    else:
        tickets = Ticket.objects.filter(created_by=request.user).order_by('-created_at')

    filter_form = TicketFilterForm(request.GET or None)
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        priority = filter_form.cleaned_data.get('priority')
        category = filter_form.cleaned_data.get('category')
        assigned_to = filter_form.cleaned_data.get('assigned_to')
        created_by = filter_form.cleaned_data.get('created_by')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')

        if status:
            tickets = tickets.filter(status=status)
        if priority:
            tickets = tickets.filter(priority=priority)
        if category:
            tickets = tickets.filter(category=category)
        if assigned_to:
            tickets = tickets.filter(assigned_to=assigned_to)
        if created_by:
            tickets = tickets.filter(created_by=created_by)
        if date_from:
            tickets = tickets.filter(created_at__date__gte=date_from)
        if date_to:
            tickets = tickets.filter(created_at__date__lte=date_to)

    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context.update({
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_tickets': tickets.count(),
        'open_tickets': tickets.filter(status='OPEN').count(),
        'in_progress_tickets': tickets.filter(status='IN_PROGRESS').count(),
    })

    return render(request, 'dashboards/employee_dashboard.html', context)



@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if not (request.user.is_superuser or
            (hasattr(request.user, 'is_admin') and request.user.is_admin) or
            (hasattr(request.user, 'is_technician') and request.user.is_technician) or
            ticket.created_by == request.user or
            ticket.assigned_to == request.user):
        messages.error(request, 'You do not have permission to view this ticket.')
        return redirect('helpdesk:dashboard')

    if request.method == 'POST' and 'comment_submit' in request.POST:
        comment_form = TicketCommentForm(request.POST, request.FILES, user=request.user, ticket=ticket)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added successfully!')
            return redirect('tickets:ticket_detail', pk=ticket.pk)
    else:
        comment_form = TicketCommentForm(user=request.user, ticket=ticket)

    if request.method == 'POST' and 'update_ticket' in request.POST:
        update_form = TicketUpdateForm(request.POST, instance=ticket)
        if update_form.is_valid():
            old_status = ticket.status
            updated_ticket = update_form.save()
            new_status = updated_ticket.status

            if old_status != new_status:
                TicketStatusChange.objects.create(
                    ticket=ticket,
                    changed_by=request.user,
                    from_status=old_status,
                    to_status=new_status
                )
            messages.success(request, 'Ticket updated successfully!')
            return redirect('tickets:ticket_detail', pk=ticket.pk)
    else:
        update_form = TicketUpdateForm(instance=ticket)

    if request.user.is_staff:
        comments = ticket.comments.all()
    else:
        comments = ticket.comments.filter(is_internal=False)

    context = {
        'ticket': ticket,
        'comments': comments,
        'comment_form': comment_form,
        'update_form': update_form,
        'status_history': ticket.status_changes.all().order_by('-changed_at'),
    }

    return render(request, 'tickets/ticket_detail.html', context)

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
    return render(request, 'tickets/my_tickets.html', context)

@login_required
def view_ticket(request, ticket_id):
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
    return render(request, 'tickets/my_tickets.html', context)


@login_required
def manage_categories(request):
    if not (request.user.is_superuser or getattr(request.user, 'is_admin', False)):
        messages.error(request, 'You do not have permission to manage categories.')
        return redirect('helpdesk:dashboard')

    # Count related tickets using the related_name
    categories = Category.objects.all().annotate(ticket_count=Count('tickets'))

    if request.method == 'POST':
        form = TicketCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('helpdesk:manage_categories')
    else:
        form = TicketCategoryForm()

    context = {
        'categories': categories,
        'form': form,
    }
    return render(request, 'helpdesk/manage_categories.html', context)

@login_required
@require_POST
def update_ticket_status(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if not (request.user.is_superuser or
            (hasattr(request.user, 'is_admin') and request.user.is_admin) or
            (hasattr(request.user, 'is_technician') and request.user.is_technician) or
            ticket.assigned_to == request.user):
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    new_status = request.POST.get('status')
    if new_status not in dict(Ticket.STATUS_CHOICES).keys():
        return JsonResponse({'success': False, 'error': 'Invalid status'})

    old_status = ticket.status
    ticket.status = new_status
    ticket.save()

    TicketStatusChange.objects.create(
        ticket=ticket,
        changed_by=request.user,
        from_status=old_status,
        to_status=new_status
    )

    return JsonResponse({
        'success': True,
        'new_status': ticket.get_status_display(),
        'status_class': new_status.lower().replace('_', '-')
    })


@login_required
def reports(request):
    if not (request.user.is_superuser or (hasattr(request.user, 'is_admin') and request.user.is_admin)):
        messages.error(request, 'You do not have permission to view reports.')
        return redirect('helpdesk:dashboard')

    tickets_by_status = (
        Ticket.objects.values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )

    tickets_by_category = (
        Ticket.objects.values('category__name')
        .annotate(count=Count('id'))
        .order_by('category__name')
    )

    tickets_by_technician = (
        Ticket.objects.filter(assigned_to__isnull=False)
        .values('assigned_to__username')
        .annotate(
            total=Count('id'),
            resolved=Count('id', filter=Q(status='RESOLVED') | Q(status='CLOSED')),
            avg_time=Avg(
                Case(
                    When(
                        Q(status='RESOLVED') | Q(status='CLOSED'),
                        then=F('resolved_at') - F('created_at')
                    ),
                    output_field=DurationField()
                )
            )
        )
        .order_by('-resolved')
    )

    context = {
        'tickets_by_status': tickets_by_status,
        'tickets_by_category': tickets_by_category,
        'tickets_by_technician': tickets_by_technician,
    }

    return render(request, 'helpdesk/reports.html', context)


@login_required
def dashboard_view(request):
    user = request.user
    context = {
        'is_admin': user.role == 'Admin' or user.is_superuser or user.is_staff,
        'is_technician': user.role == 'Technician',
        'is_employee': user.role == 'Employee',
        'current_date': timezone.now().strftime("%B %d, %Y"),
    }

    # Admin-specific stats
    if context['is_admin']:
        context.update({
            'total_tickets': Ticket.objects.all().count(),
            'open_tickets': Ticket.objects.filter(status='open').count(),
            'in_progress_tickets': Ticket.objects.filter(status='in_progress').count(),
            'resolved_tickets': Ticket.objects.filter(status='resolved').count(),
            'page_obj': Ticket.objects.all().order_by('-updated_at')[:20],  # adjust pagination logic if using Paginator
        })

    # Technician-specific stats
    elif context['is_technician']:
        context.update({
            'total_tickets': Ticket.objects.filter(assigned_to=user).count(),
            'open_tickets': Ticket.objects.filter(assigned_to=user, status='open').count(),
            'in_progress_tickets': Ticket.objects.filter(assigned_to=user, status='in_progress').count(),
            'resolved_tickets': Ticket.objects.filter(assigned_to=user, status='resolved').count(),
            'page_obj': Ticket.objects.filter(assigned_to=user).order_by('-updated_at')[:20],
        })

    # Employee-specific stats
    else:
        context.update({
            'total_tickets': Ticket.objects.filter(created_by=user).count(),
            'open_tickets': Ticket.objects.filter(created_by=user, status='open').count(),
            'in_progress_tickets': Ticket.objects.filter(created_by=user, status='in_progress').count(),
            'resolved_tickets': Ticket.objects.filter(created_by=user, status='resolved').count(),
            'page_obj': Ticket.objects.filter(created_by=user).order_by('-updated_at')[:20],
        })

    return render(request, 'dashboard.html', context)

class LandingView(TemplateView):
    template_name = 'landing.html'

def login_redirect_view(request):
    user = request.user
    if user.user_type == 'EMP':
        return redirect('employee_dashboard')
    elif user.user_type == 'TECH':
        return redirect('technician_dashboard')
    elif user.is_superuser:
        return redirect('admin_dashboard')
    else:
        return redirect('dashboard')

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


@login_required
def edit_category(request, category_id):
    category = get_object_or_404(TicketCategory, id=category_id)

    if request.method == 'POST':
        form = TicketCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('helpdesk:manage_categories')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TicketCategoryForm(instance=category)

    return render(request, 'helpdesk/edit_category.html', {
        'form': form,
        'category': category
    })

@login_required
def delete_category(request, category_id):
    category = get_object_or_404(TicketCategory, id=category_id)

    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('helpdesk:manage_categories')

    return render(request, 'helpdesk/confirm_delete_category.html', {'category': category})