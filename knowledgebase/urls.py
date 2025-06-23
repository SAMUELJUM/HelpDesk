from django.urls import path
from . import views

app_name = 'knowledgebase'

urlpatterns = [
    path('articles/', views.article_list, name='article_list'),
    path('categories/', views.category_list, name='category_list'),
    path('articles/<int:pk>/', views.article_detail, name='article_detail'),  # Keep this
    path('articles/create/', views.create_article, name='create_article'),
    path('articles/<int:pk>/edit/', views.edit_article, name='edit_article'),
    path('articles/<int:pk>/rate/', views.rate_article, name='rate_article'),
    path('articles/<int:pk>/delete/', views.delete_article, name='delete_article'),
]
