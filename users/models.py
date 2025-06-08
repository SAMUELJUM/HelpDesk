from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('ADMIN', 'Administrator'),
        ('TECH', 'Technician'),
        ('USER', 'End User'),
    )

    user_type = models.CharField(max_length=5, choices=USER_TYPE_CHOICES, default='USER')
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)  # Merged from duplicate
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

    @property
    def is_admin(self):
        return self.user_type == 'ADMIN'

    @property
    def is_technician(self):
        return self.user_type == 'TECH'

    @property
    def is_enduser(self):
        return self.user_type == 'USER'

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Single set of signal receivers (remove duplicates)
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):  # Check if profile exists
        instance.profile.save()