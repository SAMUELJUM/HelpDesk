from django import forms
from .models import Category
from.models import Department
from django import forms
from .models import Ticket, TicketCategory
from django.utils import timezone
from .models import Department, TicketComment
from django.contrib.auth import get_user_model

User = get_user_model()



class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'department', 'category', 'priority']  # Add any others you need

    department = forms.ModelChoiceField(queryset=Department.objects.all(), empty_label="Select a department")


def __init__(self, *args, **kwargs):
    self.user = kwargs.pop('user', None)  # Remove 'user' from kwargs before super()
    super().__init__(*args, **kwargs)  # Now ModelForm.__init__ won't see 'user'
    #self.fields['department'].queryset = Department.objects.all()


class TicketUpdateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['status', 'assigned_to', 'priority']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(user_type='TECH')


class TicketCategoryForm(forms.ModelForm):
    class Meta:
        model = TicketCategory
        fields = ['name', 'description', 'default_assignee']  # Include the field explicitly

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make sure the field exists before applying queryset
        if 'default_assignee' in self.fields:
            self.fields['default_assignee'].queryset = User.objects.filter(user_type__in=['TECH', 'ADMIN'])

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

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            'title',
            'category',
            'priority',
            'department',
            'description',
            'attachment',
            'is_urgent'
        ]
        # IMPORTANT: Do NOT include 'id', 'ticket_id', or 'reference_number'
        # Django and your model's save() method handle these automatically

        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter a brief description of your issue',
                'maxlength': 255,
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Please provide detailed information about your issue...',
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.txt'
            }),
            'is_urgent': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make sure required fields are marked
        self.fields['title'].required = True
        self.fields['description'].required = True
        self.fields['category'].required = True
        self.fields['priority'].required = True
        self.fields['department'].required = True

        # Set help text
        self.fields['attachment'].help_text = 'Optional: Upload supporting files (max 5MB each)'

        # Filter active categories and departments only
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)

        # Add empty choice for better UX
        self.fields['category'].empty_label = "Select a category"
        self.fields['department'].empty_label = "Select a department"

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            # Check file size (5MB limit)
            if attachment.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size cannot exceed 5MB.')
        return attachment

class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ['comment']  # <-- Correct field name from 'content' to 'comment'
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Write your comment here...'
            }),
        }
