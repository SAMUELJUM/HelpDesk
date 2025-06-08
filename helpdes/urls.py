from django.urls import path
from . import views
from users.views import register
from .views import dashboard


app_name = 'helpdes'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('tickets/create/', views.create_ticket, name='create_ticket'),
    path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:pk>/update-status/', views.update_ticket_status, name='update_ticket_status'),
    path('categories/', views.manage_categories, name='manage_categories'),
    path('reports/', views.reports, name='reports'),
    path('register/', register, name='register'),
]