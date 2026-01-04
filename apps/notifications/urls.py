"""
URL Configuration for Notifications
====================================
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Sayfa
    path('', views.notifications_page, name='notifications_page'),
    
    # API
    path('api/list/', views.get_notifications, name='get_notifications'),
    path('api/read/', views.mark_as_read, name='mark_as_read'),
    path('api/delete/', views.delete_notification, name='delete_notification'),
    path('api/unread-count/', views.get_unread_count, name='unread_count'),
    path('api/preferences/', views.notification_preferences, name='preferences'),
]

