from django import forms
from .models import KnowledgeBaseArticle, ArticleRating

class ArticleForm(forms.ModelForm):
    class Meta:
        model = KnowledgeBaseArticle
        fields = ['title', 'content', 'category', 'is_published']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
        }

class RatingForm(forms.ModelForm):
    class Meta:
        model = ArticleRating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }