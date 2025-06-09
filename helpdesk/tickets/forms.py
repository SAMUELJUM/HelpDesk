from django import forms
from .models import Ticket, TicketComment

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'priority', 'category', 'assigned_to', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Pass user when instantiating form
        super().__init__(*args, **kwargs)

        # Role-based customization
        if not (user and (user.is_superuser or user.groups.filter(name='Admin').exists())):
            self.fields.pop('assigned_to')  # Hide assigned_to for non-admins
            self.fields.pop('status')       # Hide status for non-admins

    def clean_title(self):
        title = self.cleaned_data['title']
        if Ticket.objects.filter(title__iexact=title).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A ticket with this title already exists.")
        return title


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

