"""
Signals for Notifications
=========================
Model değişikliklerinde otomatik bildirim oluşturma.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver


def run_task(task_func, *args, **kwargs):
    """
    Celery varsa async çalıştır, yoksa senkron çalıştır.
    """
    try:
        # Celery çalışıyorsa async gönder
        task_func.delay(*args, **kwargs)
    except Exception:
        # Celery yoksa veya hata varsa senkron çalıştır
        try:
            task_func(*args, **kwargs)
        except Exception as e:
            print(f"Task error: {e}")


@receiver(post_save, sender='users.Friendship')
def friendship_notification(sender, instance, created, **kwargs):
    """Arkadaşlık durumu değiştiğinde bildirim oluştur"""
    from apps.notifications.models import Notification
    
    if created and instance.status == 'pending':
        # Yeni arkadaşlık isteği - direkt bildirim oluştur
        Notification.objects.create(
            user=instance.friend,  # İsteği alan
            notification_type='friend_request',
            title='Yeni Arkadaşlık İsteği',
            message=f'{instance.user.get_full_name() or instance.user.username} sana arkadaşlık isteği gönderdi.',
            related_user=instance.user,
            action_url='/friends/',
        )
    elif not created and instance.status == 'accepted':
        # Arkadaşlık kabul edildi
        Notification.objects.create(
            user=instance.user,  # İsteği gönderen
            notification_type='friend_accepted',
            title='Arkadaşlık İsteği Kabul Edildi',
            message=f'{instance.friend.get_full_name() or instance.friend.username} arkadaşlık isteğini kabul etti.',
            related_user=instance.friend,
            action_url='/friends/',
        )


@receiver(post_save, sender='movies.Rating')
def rating_notification(sender, instance, created, **kwargs):
    """Yeni puanlama yapıldığında arkadaşlara bildirim gönder"""
    if not created:
        return
    
    from django.db.models import Q
    from apps.notifications.models import Notification, NotificationPreference
    from apps.users.models import Friendship
    
    user = instance.user
    movie = instance.movie
    
    # Kullanıcının arkadaşlarını bul
    friendships = Friendship.objects.filter(
        status='accepted'
    ).filter(
        Q(user=user) | Q(friend=user)
    )
    
    for friendship in friendships:
        # Arkadaşı belirle
        friend = friendship.friend if friendship.user == user else friendship.user
        
        # Kullanıcı tercihini kontrol et
        try:
            prefs = friend.notification_preferences
            if not prefs.push_friend_ratings:
                continue
        except NotificationPreference.DoesNotExist:
            pass
        
        # Bildirim oluştur
        Notification.objects.create(
            user=friend,
            notification_type='new_rating',
            title='Arkadaşın Film Puanladı',
            message=f'{user.get_full_name() or user.username} "{movie.title}" filmine {instance.score}/10 puan verdi.',
            related_user=user,
            related_movie_id=movie.id,
            action_url=f'/movie/{movie.id}/',
        )


@receiver(post_save, sender='users.User')
def create_notification_preferences(sender, instance, created, **kwargs):
    """Yeni kullanıcı oluşturulduğunda bildirim tercihlerini oluştur"""
    if created:
        from apps.notifications.models import NotificationPreference
        NotificationPreference.objects.get_or_create(user=instance)
