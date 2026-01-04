"""
Views for Notifications
=======================
Bildirim görüntüleme ve yönetim view'ları.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json

from .models import Notification, NotificationPreference


@login_required
def notifications_page(request):
    """Bildirimler sayfası"""
    # Önce okunmamış sayısını al (slice'dan önce)
    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    # Sonra slice ile bildirimleri al
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:50]
    
    return render(request, 'notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@login_required
@require_http_methods(["GET"])
def get_notifications(request):
    """
    API: Kullanıcı bildirimlerini getir
    
    Query params:
        - unread_only: true/false (sadece okunmamışları getir)
        - limit: int (maksimum bildirim sayısı)
    """
    unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
    limit = min(int(request.GET.get('limit', 20)), 100)
    
    notifications = Notification.objects.filter(user=request.user)
    
    if unread_only:
        notifications = notifications.filter(is_read=False)
    
    notifications = notifications.order_by('-created_at')[:limit]
    
    data = []
    for n in notifications:
        data.append({
            'id': n.id,
            'type': n.notification_type,
            'title': n.title,
            'message': n.message,
            'action_url': n.action_url,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat(),
            'related_user_id': n.related_user_id,
            'related_movie_id': n.related_movie_id,
        })
    
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return JsonResponse({
        'success': True,
        'notifications': data,
        'unread_count': unread_count,
    })


@login_required
@require_http_methods(["POST"])
def mark_as_read(request):
    """
    API: Bildirimi okundu olarak işaretle
    
    Body:
        - notification_id: int (tek bildirim)
        - notification_ids: list[int] (birden fazla bildirim)
        - all: true (tümünü okundu işaretle)
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    if data.get('all'):
        # Tümünü okundu işaretle
        updated = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return JsonResponse({
            'success': True,
            'updated_count': updated,
        })
    
    notification_ids = data.get('notification_ids', [])
    if data.get('notification_id'):
        notification_ids.append(data['notification_id'])
    
    if not notification_ids:
        return JsonResponse({'success': False, 'error': 'No notification IDs provided'}, status=400)
    
    updated = Notification.objects.filter(
        user=request.user,
        id__in=notification_ids,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    return JsonResponse({
        'success': True,
        'updated_count': updated,
    })


@login_required
@require_http_methods(["POST"])
def delete_notification(request):
    """
    API: Bildirimi sil
    
    Body:
        - notification_id: int
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    notification_id = data.get('notification_id')
    if not notification_id:
        return JsonResponse({'success': False, 'error': 'notification_id required'}, status=400)
    
    deleted, _ = Notification.objects.filter(
        user=request.user,
        id=notification_id
    ).delete()
    
    return JsonResponse({
        'success': True,
        'deleted': deleted > 0,
    })


@login_required
@require_http_methods(["GET"])
def get_unread_count(request):
    """API: Okunmamış bildirim sayısını getir"""
    count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    return JsonResponse({
        'success': True,
        'unread_count': count,
    })


@login_required
@require_http_methods(["GET", "POST"])
def notification_preferences(request):
    """
    API: Bildirim tercihlerini getir/güncelle
    """
    prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'preferences': {
                'email_friend_requests': prefs.email_friend_requests,
                'email_recommendations': prefs.email_recommendations,
                'email_weekly_digest': prefs.email_weekly_digest,
                'email_upcoming_movies': prefs.email_upcoming_movies,
                'push_friend_requests': prefs.push_friend_requests,
                'push_friend_ratings': prefs.push_friend_ratings,
                'push_recommendations': prefs.push_recommendations,
            }
        })
    
    # POST: Tercihleri güncelle
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    # Güncelle
    fields_to_update = []
    for field in ['email_friend_requests', 'email_recommendations', 'email_weekly_digest',
                  'email_upcoming_movies', 'push_friend_requests', 'push_friend_ratings',
                  'push_recommendations']:
        if field in data:
            setattr(prefs, field, bool(data[field]))
            fields_to_update.append(field)
    
    if fields_to_update:
        prefs.save(update_fields=fields_to_update)
    
    return JsonResponse({
        'success': True,
        'message': 'Preferences updated',
    })
