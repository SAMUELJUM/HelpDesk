from django.conf import settings
from django.db import models
from django.utils import timezone
import uuid
from django.contrib.auth import get_user_model

User = get_user_model()


class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    # Django will automatically create an 'id' field as primary key
    ticket_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    reference_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        blank=True,
        null=True
    )

    title = models.CharField(max_length=255)
    description = models.TextField(help_text="Provide a detailed description of the issue.")

    category = models.ForeignKey('tickets.Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    attachment = models.FileField(upload_to='ticket_attachments/', null=True, blank=True)
    is_urgent = models.BooleanField(default=False, help_text="Mark if this ticket needs urgent attention")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets_created'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_assigned'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference_number or 'TCK-??????'}: {self.title}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            # Generate reference number only if it doesn't exist
            prefix = "TCK"
            unique_part = uuid.uuid4().hex[:6].upper()
            self.reference_number = f"{prefix}-{unique_part}"

            # Ensure uniqueness
            while Ticket.objects.filter(reference_number=self.reference_number).exists():
                unique_part = uuid.uuid4().hex[:6].upper()
                self.reference_number = f"{prefix}-{unique_part}"

        super().save(*args, **kwargs)

    def mark_resolved(self):
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save()

    def mark_closed(self):
        self.status = 'closed'
        self.closed_at = timezone.now()
        self.save()

    @property
    def is_overdue(self):
        if self.due_by and self.status in ['OPEN', 'IN_PROGRESS']:
            return timezone.now() > self.due_by
        return False


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



class TicketCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    default_assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='category_assigned'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Ticket Categories"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    default_assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_categories',
        limit_choices_to={'role': 'admin,technician'},
        help_text="Optional: Assign a default technician to handle tickets in this category."
    )

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class TicketComment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ticket_comments'
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.ticket}"