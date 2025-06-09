from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Ticket, TicketComment
from .forms import TicketForm, TicketCommentForm
from django.contrib.auth.models import User, Group
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, user_passes_test


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



@login_required
def create_ticket(request):
        form = TicketForm(request.POST or None, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            return redirect('tickets:ticket_list')
        return render(request, 'tickets/ticket_form.html', {'form': form})

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

    technicians = User.objects.filter(groups__name='Technician')
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

    technicians = User.objects.filter(role='technician')  # or use is_staff, group, etc.

    if request.method == "POST" and request.user.is_staff:
        ticket.status = request.POST.get("status")
        tech_id = request.POST.get("technician")
        ticket.assigned_to = User.objects.get(id=tech_id) if tech_id else None
        ticket.save()
        return redirect("view_ticket", ticket_id=ticket.id)

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