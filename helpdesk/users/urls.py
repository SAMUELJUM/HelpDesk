from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from .views import change_password

app_name = 'users'

urlpatterns = [
    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='landing.html'
    ), name='logout'),

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

    # Role-Based Dashboards
    path('admin/dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('technician/dashboard', views.technician_dashboard, name='technician_dashboard'),
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

]