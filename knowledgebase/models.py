from django.db import models
from django.urls import reverse
from helpdes.models import TicketCategory
from django.contrib.auth import get_user_model

User = get_user_model()

class ArticleCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class KnowledgeBaseArticle(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.ForeignKey('ArticleCategory', on_delete=models.SET_NULL, null=True, blank=True)
    related_ticket_categories = models.ManyToManyField(
        TicketCategory,
        blank=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE, related_name='+'
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)
    helpful_yes = models.PositiveIntegerField(default=0)
    helpful_no = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ['-last_updated']

    def __str__(self):
        return self.title

class ArticleRating(models.Model):
        article = models.ForeignKey('KnowledgeBaseArticle', on_delete=models.CASCADE, related_name='ratings')
        user = models.ForeignKey(User, on_delete=models.CASCADE)
        rating = models.PositiveSmallIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])
        comment = models.TextField(blank=True)
        created_at = models.DateTimeField(auto_now_add=True)

        class Meta:
            unique_together = ('article', 'user')

        def __str__(self):
            return f"{self.rating} stars by {self.user.username}"

class KnowledgeBaseCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name



    def get_absolute_url(self):
        return reverse('knowledgebase:article_detail', kwargs={'pk': self.pk})



    @property
    def helpfulness_ratio(self):
        if self.helpful_yes + self.helpful_no == 0:
            return 0
        return (self.helpful_yes / (self.helpful_yes + self.helpful_no)) * 100