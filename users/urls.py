from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from .views import landing, manage_users, activate_account
from .views import change_password

app_name = 'users'

urlpatterns = [
    # Authentication URLs
    path('manage-users/', manage_users, name='manage_users'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('', views.landing, name='landing'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='landing'
    ), name='logout'),
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate'),

    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    # Password Reset
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='users/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'),
         name='password_reset_complete'),
    path('change-password/', change_password, name='change_password'),

    # Dashboard Redirect
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('redirect/', views.role_based_redirect, name='role_redirect'),

    # Role-Based Dashboards
    path('dashboard/admin', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/technician', views.technician_dashboard, name='technician_dashboard'),
    path('employee/dashboard', views.employee_dashboard, name='employee_dashboard'),

    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile, name='profile_update'),  # You can create a dedicated view later

    # User Management
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:pk>/', views.user_detail_view, name='user_detail'),
    path('users/<int:pk>/update/', views.user_update_view, name='user_update'),
    path('tickets/', include('tickets.urls')),
    path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('my-tickets/', views.my_tickets_view, name='my_tickets'),
    path('tickets/', views.ticket_list, name='ticket_list'),


]