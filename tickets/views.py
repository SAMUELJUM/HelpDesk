from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Ticket, TicketComment
from .forms import TicketForm, TicketCommentForm
from django.utils import timezone
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from tickets.models import Ticket
from tickets.forms import TicketCategoryForm
from tickets.models import TicketCategory
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(created_by=request.user).order_by('-created_at')

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
        'tickets': tickets_page,  # Paginated and updated
        'query': query,
        'status_filter': status_filter,
    })

@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    comment_form = TicketCommentForm(request.POST or None)

    if request.method == 'POST' and comment_form.is_valid():
        comment = comment_form.save(commit=False)
        comment.ticket = ticket
        comment.commented_by = request.user
        comment.save()
        return redirect('tickets:ticket_detail', pk=pk)

    return render(request, 'tickets/ticket_detail.html', {
        'ticket': ticket,
        'comment_form': comment_form
    })


# Alternative view with additional error handling
@login_required
def create_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                # Additional validation can be added here
                cleaned_data = form.cleaned_data

                # Create and save ticket
                ticket = Ticket.objects.create(
                    title=cleaned_data['title'],
                    description=cleaned_data['description'],
                    category=cleaned_data['category'],
                    department=cleaned_data['department'],
                    priority=cleaned_data['priority'],
                    attachment=cleaned_data.get('attachment'),
                    is_urgent=cleaned_data.get('is_urgent', False),
                    created_by=request.user,
                )

                messages.success(
                    request,
                    f'Support ticket {ticket.reference_number} has been created successfully! '
                    f'You will receive updates via email.'
                )
                return redirect('tickets:ticket_detail', pk=ticket.pk)

            except Exception as e:
                messages.error(request, f'An error occurred while creating your ticket: {str(e)}')
                print(f"Ticket creation error: {e}")  # For debugging
        else:
            messages.error(request, 'Please correct the form errors below.')
    else:
        form = TicketForm()

    context = {
        'form': form,
        'page_title': 'Create Support Ticket'
    }
    return render(request, 'tickets/create_ticket.html', context)

@login_required
def ticket_update(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    form = TicketForm(request.POST or None, instance=ticket, user=request.user)
    if form.is_valid():
        form.save()
        return redirect('tickets:ticket_detail', pk=pk)
    return render(request, 'tickets/ticket_form.html', {'form': form})

@login_required
def ticket_edit(request, pk):
    """Edit an existing ticket"""
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.user != ticket.created_by and not request.user.is_superuser:
        messages.error(request, "Unauthorized action.")
        return redirect('tickets:ticket_list')

    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, "Ticket updated successfully!")
            return redirect('tickets:ticket_detail', pk=pk)
    else:
        form = TicketForm(instance=ticket)

    return render(request, 'tickets/ticket_form.html', {'form': form, 'title': 'Edit Ticket'})


@login_required
def ticket_delete(request, pk):
    """Delete a ticket"""
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.user != ticket.created_by and not request.user.is_superuser:
        messages.error(request, "You can't delete this ticket.")
        return redirect('tickets:ticket_list')

    ticket.delete()
    messages.success(request, "Ticket deleted.")
    return redirect('tickets:ticket_list')


@login_required
def ticket_add_comment(request, pk):
    """Add a comment to a ticket"""
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == 'POST':
        form = TicketCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.commented_by = request.user
            comment.save()
            messages.success(request, "Comment added.")
        else:
            messages.error(request, "Error adding comment.")

    return redirect('tickets:ticket_detail', pk=pk)


@login_required
def ticket_update_status(request, pk):
    """Technician updates ticket status"""
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.user != ticket.assigned_to:
        messages.error(request, "Only assigned technicians can update status.")
        return redirect('tickets:ticket_detail', pk=pk)

    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['Open', 'In Progress', 'Resolved', 'Closed']:
            ticket.status = status
            ticket.save()
            messages.success(request, f"Ticket marked as '{status}'.")
        else:
            messages.error(request, "Invalid status.")

    return redirect('tickets:ticket_detail', pk=pk)




def is_admin(user):
    return user.is_superuser or user.groups.filter(name='Admin').exists()

@login_required
@user_passes_test(is_admin)
def assign_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    if request.method == 'POST':
        technician_id = request.POST.get('technician')
        if technician_id:
            technician = get_object_or_404(User, pk=technician_id)
            ticket.assigned_to = technician
            ticket.save()
            messages.success(request, f'Ticket assigned to {technician.username}.')
        return redirect('tickets:ticket_detail', pk=pk)

    # Debug log
    technicians = User.objects.filter(groups__name='Technician')
    print("Found technicians:", technicians)

    #technicians = User.objects.filter(groups__name='Technician')
    return render(request, 'tickets/assign_ticket.html', {
        'ticket': ticket,
        'technicians': technicians
    })


@login_required
def add_comment(request, ticket_pk):
    ticket = get_object_or_404(Ticket, pk=ticket_pk)

    if request.method == 'POST':
        form = TicketCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added successfully.')
            return redirect('tickets:ticket_detail', pk=ticket_pk)
    else:
        form = TicketCommentForm()

    return render(request, 'tickets/add_comment.html', {
        'form': form,
        'ticket': ticket,
    })


def view_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    technicians = User.objects.filter(role='technician')

    if request.method == "POST" and request.user.is_staff:
        ticket.status = request.POST.get("status")
        tech_id = request.POST.get("technician")
        ticket.assigned_to = User.objects.get(id=tech_id) if tech_id else None
        ticket.save()

        # ✅ Use reverse to avoid NoReverseMatch
        return redirect(reverse("view_ticket", args=[ticket.id]))

    return render(request, "tickets/view_ticket.html", {
        "ticket": ticket,
        "technicians": technicians
    })

@login_required
def submit_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            return redirect('my_tickets')  # Redirect to a "My Tickets" page or success page
    else:
        form = TicketForm()
    return render(request, 'tickets/submit_ticket.html', {'form': form})



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

def edit_category(request, category_id):
        category = get_object_or_404(TicketCategory, id=category_id)

        if request.method == 'POST':
            form = TicketCategoryForm(request.POST, instance=category)
            if form.is_valid():
                form.save()
                return redirect('manage_categories')  # Or wherever you want
        else:
            form = TicketCategoryForm(instance=category)

        return render(request, 'helpdesk/edit_category.html', {'form': form, 'category': category})