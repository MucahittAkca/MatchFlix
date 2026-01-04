"""
Celery Tasks for Notifications
==============================
Asenkron bildirim görevleri.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


@shared_task(bind=True, max_retries=3)
def send_notification_email(self, notification_id: int):
    """
    Bildirim e-postası gönder
    
    Args:
        notification_id: Notification model ID
    """
    from apps.notifications.models import Notification
    
    try:
        notification = Notification.objects.select_related('user').get(id=notification_id)
        user = notification.user
        
        # Kullanıcının e-posta tercihi kontrol et
        prefs = getattr(user, 'notification_preferences', None)
        if prefs:
            # Bildirim tipine göre tercih kontrolü
            pref_map = {
                'friend_request': prefs.email_friend_requests,
                'friend_accepted': prefs.email_friend_requests,
                'recommendation': prefs.email_recommendations,
                'weekly_digest': prefs.email_weekly_digest,
                'upcoming_movie': prefs.email_upcoming_movies,
            }
            if not pref_map.get(notification.notification_type, True):
                return {'status': 'skipped', 'reason': 'user_preference'}
        
        # E-posta gönder
        subject = f"MatchFlix: {notification.title}"
        
        # HTML template (opsiyonel)
        try:
            html_message = render_to_string('emails/notification.html', {
                'notification': notification,
                'user': user,
                'site_url': settings.SITE_URL,
            })
        except Exception:
            html_message = None
        
        send_mail(
            subject=subject,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # E-posta gönderildi olarak işaretle
        notification.is_email_sent = True
        notification.save(update_fields=['is_email_sent'])
        
        return {'status': 'sent', 'email': user.email}
        
    except Notification.DoesNotExist:
        return {'status': 'error', 'reason': 'notification_not_found'}
    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc, countdown=60 * 5)  # 5 dakika sonra tekrar dene


@shared_task
def create_friend_request_notification(from_user_id: int, to_user_id: int):
    """Arkadaşlık isteği bildirimi oluştur"""
    from apps.notifications.models import Notification
    from apps.users.models import User
    
    try:
        from_user = User.objects.get(id=from_user_id)
        to_user = User.objects.get(id=to_user_id)
        
        notification = Notification.objects.create(
            user=to_user,
            notification_type='friend_request',
            title='Yeni Arkadaşlık İsteği',
            message=f'{from_user.get_full_name() or from_user.username} sana arkadaşlık isteği gönderdi.',
            related_user=from_user,
            action_url='/friends/',
        )
        
        # E-posta gönder (async)
        send_notification_email.delay(notification.id)
        
        return {'status': 'created', 'notification_id': notification.id}
        
    except User.DoesNotExist:
        return {'status': 'error', 'reason': 'user_not_found'}


@shared_task
def create_friend_accepted_notification(from_user_id: int, to_user_id: int):
    """Arkadaşlık kabul bildirimi oluştur"""
    from apps.notifications.models import Notification
    from apps.users.models import User
    
    try:
        from_user = User.objects.get(id=from_user_id)
        to_user = User.objects.get(id=to_user_id)
        
        notification = Notification.objects.create(
            user=to_user,
            notification_type='friend_accepted',
            title='Arkadaşlık İsteği Kabul Edildi',
            message=f'{from_user.get_full_name() or from_user.username} arkadaşlık isteğini kabul etti.',
            related_user=from_user,
            action_url=f'/profile/{from_user.id}/',
        )
        
        return {'status': 'created', 'notification_id': notification.id}
        
    except User.DoesNotExist:
        return {'status': 'error', 'reason': 'user_not_found'}


@shared_task
def create_friend_rating_notification(user_id: int, friend_id: int, movie_id: int, movie_title: str, score: int):
    """Arkadaş puanlama bildirimi oluştur"""
    from apps.notifications.models import Notification, NotificationPreference
    from apps.users.models import User
    
    try:
        user = User.objects.get(id=user_id)
        friend = User.objects.get(id=friend_id)
        
        # Kullanıcı tercihini kontrol et
        try:
            prefs = user.notification_preferences
            if not prefs.push_friend_ratings:
                return {'status': 'skipped', 'reason': 'user_preference'}
        except NotificationPreference.DoesNotExist:
            pass
        
        notification = Notification.objects.create(
            user=user,
            notification_type='new_rating',
            title='Arkadaşın Film Puanladı',
            message=f'{friend.get_full_name() or friend.username} "{movie_title}" filmine {score}/10 puan verdi.',
            related_user=friend,
            related_movie_id=movie_id,
            action_url=f'/movie/{movie_id}/',
        )
        
        return {'status': 'created', 'notification_id': notification.id}
        
    except User.DoesNotExist:
        return {'status': 'error', 'reason': 'user_not_found'}


@shared_task
def check_upcoming_movies():
    """
    Yakında vizyona girecek filmleri kontrol et ve bildirim oluştur.
    Watchlist'teki filmler için çalışır.
    (Günde bir kez çalıştırılmalı - Celery Beat ile)
    """
    from apps.notifications.models import Notification
    from apps.movies.models import Movie, Watchlist
    from apps.users.models import User
    from datetime import date
    
    # Önümüzdeki 7 gün içinde vizyona girecek filmler
    today = date.today()
    upcoming_date = today + timedelta(days=7)
    
    upcoming_movies = Movie.objects.filter(
        release_date__gte=today,
        release_date__lte=upcoming_date
    )
    
    notifications_created = 0
    
    for movie in upcoming_movies:
        # Bu filmi watchlist'inde tutanlar
        watchlist_users = Watchlist.objects.filter(
            movie=movie
        ).select_related('user')
        
        for wl in watchlist_users:
            # Bu film için daha önce bildirim gönderilmiş mi?
            existing = Notification.objects.filter(
                user=wl.user,
                notification_type='upcoming_movie',
                related_movie_id=movie.id,
                created_at__gte=timezone.now() - timedelta(days=7)
            ).exists()
            
            if not existing:
                days_until = (movie.release_date - today).days
                
                Notification.objects.create(
                    user=wl.user,
                    notification_type='upcoming_movie',
                    title='Listendeki Film Yakında Vizyonda!',
                    message=f'"{movie.title}" {days_until} gün içinde vizyona giriyor.',
                    related_movie_id=movie.id,
                    action_url=f'/movie/{movie.id}/',
                )
                notifications_created += 1
    
    return {'status': 'completed', 'notifications_created': notifications_created}


@shared_task
def send_weekly_recommendations():
    """
    Haftalık öneri e-postası gönder.
    (Haftada bir kez çalıştırılmalı - Celery Beat ile)
    """
    from apps.notifications.models import Notification, NotificationPreference
    from apps.users.models import User
    from apps.movies.models import Movie
    
    # Aktif kullanıcıları al (son 30 günde giriş yapmış)
    active_users = User.objects.filter(
        last_login__gte=timezone.now() - timedelta(days=30)
    )
    
    notifications_created = 0
    
    for user in active_users:
        # E-posta tercihini kontrol et
        try:
            prefs = user.notification_preferences
            if not prefs.email_weekly_digest:
                continue
        except NotificationPreference.DoesNotExist:
            pass
        
        # Popüler filmlerden öner (basit versiyon)
        # TODO: Gerçek öneri algoritması eklenecek
        recommended_movies = Movie.objects.order_by('-popularity')[:5]
        
        if recommended_movies:
            movie_list = ", ".join([m.title for m in recommended_movies[:3]])
            
            notification = Notification.objects.create(
                user=user,
                notification_type='weekly_digest',
                title='Bu Hafta Senin İçin Seçtiklerimiz',
                message=f'Bu hafta {movie_list} ve daha fazlasını kaçırma!',
                action_url='/explore/',
            )
            
            # E-posta gönder
            send_notification_email.delay(notification.id)
            notifications_created += 1
    
    return {'status': 'completed', 'notifications_created': notifications_created}


@shared_task
def cleanup_old_notifications(days: int = 90):
    """
    Eski bildirimleri temizle.
    
    Args:
        days: Kaç günden eski bildirimler silinecek
    """
    from apps.notifications.models import Notification
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Okunmuş ve eski bildirimleri sil
    deleted_count, _ = Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff_date
    ).delete()
    
    return {'status': 'completed', 'deleted_count': deleted_count}

