from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.ticket_list, name='ticket_list'),
    path('create/', views.create_ticket, name='create_ticket'),
    path('<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('<int:pk>/update/', views.ticket_update, name='ticket_update'),
    path('<int:pk>/delete/', views.ticket_delete, name='ticket_delete'),
    path('<int:pk>/assign/', views.assign_ticket, name='assign_ticket'),
    path('<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('', views.ticket_list, name='ticket_list'),
    path('<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('submit/', views.submit_ticket, name='submit_ticket'),
    path('ticket/<int:ticket_id>/', views.view_ticket, name='view_ticket'),

]
