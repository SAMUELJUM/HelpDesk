from django.urls import path
from django.contrib.auth import views as auth_views
from .views import register, user_update
from . import views
from .views import user_login, dashboard_redirect
from django.contrib.auth import get_user_model

User = get_user_model()

app_name = 'users'

urlpatterns = [
    # Authentication URLs
    path('register/', register, name='register'),
    path('login/', views.login_view, name='login'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    #path('register/', views.register, name='register'),
    path('login/', user_login, name='login'),
    path('dashboard/', dashboard_redirect, name='dashboard'),

    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    #path('logout/', views.logout_view, name='logout'),
    # Password reset URLs
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

    # Profile URLs
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile, name='profile_update'),

    # User management URLs (for admin/technicians)
    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/update/', views.user_update, name='user_update'),
    path('users/<int:pk>/update/', user_update, name='user_update'),
]