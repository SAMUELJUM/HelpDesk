from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.views.generic import TemplateView


from django.utils import timezone

from .models import Ticket, TicketComment, TicketCategory, TicketStatusChange
from .forms import (
    TicketForm,
    TicketUpdateForm,
    TicketCommentForm,
    TicketCategoryForm,
    TicketFilterForm
)
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def dashboard(request):
    # Initialize context and tickets early
    context = {}
    tickets = Ticket.objects.none()  # Default empty queryset

    # Admin dashboard shows all tickets
    if request.user.is_admin:
        tickets = Ticket.objects.all().order_by('-created_at')

    # Technician dashboard shows assigned tickets
    elif request.user.is_technician:
        tickets = Ticket.objects.filter(
            Q(assigned_to=request.user) | Q(status='OPEN')
        ).order_by('-created_at')

    # Staff/End-user dashboard logic
    elif request.user.is_staff:
        tickets = Ticket.objects.all().order_by('-created_at')
    else:
        tickets = Ticket.objects.filter(created_by=request.user).order_by('-created_at')

    # Apply filters if any
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

    # Pagination
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Update context (now guaranteed to run for all users)
    context.update({
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_tickets': tickets.count(),
        'open_tickets': tickets.filter(status='OPEN').count(),
        'in_progress_tickets': tickets.filter(status='IN_PROGRESS').count(),
    })

    return render(request, 'dashboard.html', context)


@login_required
def create_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()

            # Create initial status change record
            TicketStatusChange.objects.create(
                ticket=ticket,
                changed_by=request.user,
                from_status='',
                to_status='OPEN'
            )

            messages.success(request, 'Ticket created successfully!')
            return redirect('helpdesk:ticket_detail', pk=ticket.pk)
    else:
        form = TicketForm(user=request.user)

    return render(request, 'helpdesk/create_ticket.html', {'form': form})


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    # Check permission to view ticket
    if not (request.user.is_admin or
            request.user.is_technician or
            ticket.created_by == request.user or
            ticket.assigned_to == request.user):
        messages.error(request, 'You do not have permission to view this ticket.')
        return redirect('helpdesk:dashboard')

    # Handle comment submission
    if request.method == 'POST':
        comment_form = TicketCommentForm(request.POST, request.FILES, user=request.user, ticket=ticket)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user
            comment.save()

            # Notify other participants
            # (Implementation depends on your notification system)

            messages.success(request, 'Comment added successfully!')
            return redirect('helpdesk:ticket_detail', pk=ticket.pk)
    else:
        comment_form = TicketCommentForm(user=request.user, ticket=ticket)

    # Handle ticket update
    if request.method == 'POST' and 'update_ticket' in request.POST:
        update_form = TicketUpdateForm(request.POST, instance=ticket)
        if update_form.is_valid():
            old_status = ticket.status
            updated_ticket = update_form.save()
            new_status = updated_ticket.status

            # Record status change if it changed
            if old_status != new_status:
                TicketStatusChange.objects.create(
                    ticket=ticket,
                    changed_by=request.user,
                    from_status=old_status,
                    to_status=new_status
                )

            messages.success(request, 'Ticket updated successfully!')
            return redirect('helpdesk:ticket_detail', pk=ticket.pk)
    else:
        update_form = TicketUpdateForm(instance=ticket)

    # Get all comments (internal comments only visible to staff)
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

    return render(request, 'helpdesk/ticket_detail.html', context)


@login_required
def manage_categories(request):
    if not request.user.is_admin:
        messages.error(request, 'You do not have permission to manage categories.')
        return redirect('helpdesk:dashboard')

    categories = TicketCategory.objects.all().annotate(
        ticket_count=Count('ticket')
    )

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

    # Check permission
    if not (request.user.is_admin or
            request.user.is_technician or
            ticket.assigned_to == request.user):
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    new_status = request.POST.get('status')
    if new_status not in dict(Ticket.STATUS_CHOICES).keys():
        return JsonResponse({'success': False, 'error': 'Invalid status'})

    old_status = ticket.status
    ticket.status = new_status
    ticket.save()

    # Record status change
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
    if not request.user.is_admin:
        messages.error(request, 'You do not have permission to view reports.')
        return redirect('helpdesk:dashboard')

    # Basic report data
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
    context = {
        'title': 'Dashboard',
        # Add any other context data you need
    }
    return render(request, 'helpdesk/dashboard.html', context)

class LandingView(TemplateView):
    template_name = 'landing.html'