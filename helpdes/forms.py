from django import forms
from .models import Ticket, TicketComment,TicketCategory
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()



class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = TicketCategory.objects.all()
        self.fields['priority'].initial = 3  # Medium priority


class TicketUpdateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['status', 'assigned_to', 'priority']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(user_type='TECH')


class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ['text', 'is_internal', 'attachment']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.ticket = kwargs.pop('ticket', None)
        super().__init__(*args, **kwargs)


class TicketCategoryForm(forms.ModelForm):
    class Meta:
        model = TicketCategory
        fields = ['name', 'description', 'sla_hours', 'default_assignee']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['default_assignee'].queryset = User.objects.filter(user_type='TECH')


class TicketFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
        ('NEED_INFO', 'Need More Info'),
    ]

    PRIORITY_CHOICES = [
        ('', 'All Priorities'),
        (1, 'Critical'),
        (2, 'High'),
        (3, 'Medium'),
        (4, 'Low'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    category = forms.ModelChoiceField(
        queryset=TicketCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type='TECH'),
        required=False,
        empty_label="All Technicians",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    created_by = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label="All Users",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )