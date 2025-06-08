from django.db import models
from django.utils import timezone
from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()


class TicketCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    sla_hours = models.PositiveIntegerField(default=24, help_text="SLA in hours")
    default_assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'user_type': 'TECH'}
    )

    def __str__(self):
        return self.name


class Ticket(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
        ('NEED_INFO', 'Need More Info'),
    )

    PRIORITY_CHOICES = (
        (1, 'Critical'),
        (2, 'High'),
        (3, 'Medium'),
        (4, 'Low'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey(
        User,
        related_name='created_tickets',
        on_delete=models.CASCADE
    )
    assigned_to = models.ForeignKey(
        User,
        related_name='assigned_tickets',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'user_type': 'TECH'}
    )
    category = models.ForeignKey(
        TicketCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPEN'
    )
    priority = models.PositiveSmallIntegerField(
        choices=PRIORITY_CHOICES,
        default=3
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    due_by = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ("can_view_all_tickets", "Can view all tickets"),
            ("can_assign_tickets", "Can assign tickets"),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # Set due_by based on SLA when category is set
        if self.category and not self.due_by and self.status == 'OPEN':
            self.due_by = timezone.now() + timezone.timedelta(hours=self.category.sla_hours)

        # Set resolved_at when status changes to RESOLVED
        if self.status == 'RESOLVED' and not self.resolved_at:
            self.resolved_at = timezone.now()

        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.due_by and self.status in ['OPEN', 'IN_PROGRESS']:
            return timezone.now() > self.due_by
        return False


class TicketComment(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        related_name='comments',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    text = models.TextField()
    is_internal = models.BooleanField(
        default=False,
        help_text="If checked, this comment will only be visible to staff"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(
        upload_to='ticket_attachments/',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.ticket}"


class TicketStatusChange(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        related_name='status_changes',
        on_delete=models.CASCADE
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.ticket}: {self.from_status} → {self.to_status}"