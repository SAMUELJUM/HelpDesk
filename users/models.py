from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    ROLE_CHOICES = (
        ('Admin', 'Admin'),
        ('Technician', 'Technician'),
        ('Employee', 'Employee'),
    )
    USER_TYPE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('TECH', 'Technician'),
        ('EMP', 'Employee'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Employee')
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='EMP')
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

    # Role properties
    @property
    def is_admin(self):
        return self.user_type == 'ADMIN'

    @property
    def is_technician(self):
        return self.user_type == 'TECH'

    @property
    def is_employee(self):
        return self.user_type == 'EMP'

    @property
    def role_name(self):
        return dict(self.USER_TYPE_CHOICES).get(self.user_type, 'Unknown')


# Profile for extra optional data (if needed)
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# Automatically create or update Profile when User is created or saved
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


# Ticket system
class Ticket(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    title = models.CharField(max_length=200)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def latest_update(self):
        return self.updates.order_by('-created_at').first()

    def __str__(self):
        return f"Ticket #{self.id} - {self.title}"


class TicketUpdate(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='updates')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Update for Ticket #{self.ticket.id}"