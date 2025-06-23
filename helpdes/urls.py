from django.urls import path
from . import views
from users.views import register
from .views import dashboard


app_name = 'helpdes'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    #path('tickets/create/', views.create_ticket, name='create_ticket'),
    path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:pk>/update-status/', views.update_ticket_status, name='update_ticket_status'),
    path('categories/', views.manage_categories, name='manage_categories'),
    path('reports/', views.reports, name='reports'),
    path('reports/export/', views.export_reports_csv, name='export_reports_csv'),
    path('reporting/', views.reporting_view, name='reporting'),
    path('register/', register, name='register'),
    path('tickets/', views.my_tickets_view, name='my_tickets'),
    path('ticket/<int:ticket_id>/', views.view_ticket, name='view_ticket'),
    path('categories/', views.manage_categories, name='manage_categories'),
    path('categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
]