from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': (
                'user_type',
                'department',
                'phone',
                'profile_picture',
            ),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'classes': ('wide',),
            'fields': (
                'user_type',
                'department',
                'phone',
                'profile_picture',
            ),
        }),
    )

    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'department', 'is_staff')
    list_filter = ('user_type', 'department', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'department')
    ordering = ('username',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'profile_picture')
    search_fields = ('user__username', 'phone_number')
