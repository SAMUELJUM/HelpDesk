from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from helpdes.views import LandingView, reporting_view
from users import views as user_views
from helpdes import views as helpdesk_views

urlpatterns = [
    path('admin/', admin.site.urls),
    #path('manage-users/', user_views.manage_users, name='manage_users'),
    path('', LandingView.as_view(), name='landing'),
    path('accounts/', include('django.contrib.auth.urls')),

    # User auth
    path('register/', user_views.register, name='register'),
    path('profile/', user_views.profile, name='profile'),
    path('dashboard/', user_views.dashboard_redirect, name='dashboard'),
    path('dashboard/admin/', user_views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/technician/', user_views.technician_dashboard, name='technician_dashboard'),
    path('dashboard/user/', user_views.user_dashboard, name='employee_dashboard'),


    # App includes
    path('users/', include(('users.urls', 'users'), namespace='users')),
    path('helpdesk/', include(('helpdes.urls', 'helpdesk'), namespace='helpdesk')),
    path('knowledgebase/', include(('knowledgebase.urls', 'knowledgebase'), namespace='knowledgebase')),
    path('tickets/', include(('tickets.urls', 'tickets'), namespace='tickets')),

    # Helpdesk-specific views
    path('manage-users/', user_views.manage_users, name='manage_users'),
    path('technician/my-tickets/', helpdesk_views.my_tickets_view, name='my_tickets'),
    path('technician/my-tickets/', helpdesk_views.my_tickets_view, name='my_tickets'),
    #path('admin/manage-users/', helpdesk_views.manage_users_view, name='manage_users'),
    path('reporting/', helpdesk_views.reporting_view, name='reporting'),
    path('admin/user/<int:pk>/', user_views.user_detail_view, name='user_detail'),
    path('admin/user/<int:pk>/edit/', user_views.user_update_view, name='user_update'),
    path('reports/export/', helpdesk_views.export_reports_csv, name='export_reports_csv'),
    path('categories/edit/<int:category_id>/', helpdesk_views.edit_category, name='edit_category'),

    # Login/logout
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),

    # Password reset
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
