"""
Notification Models for MatchFlix
=================================
Kullanıcı bildirimleri için modeller.
"""

from django.db import models
from django.conf import settings


class Notification(models.Model):
    """Kullanıcı bildirimi"""
    
    class NotificationType(models.TextChoices):
        FRIEND_REQUEST = 'friend_request', 'Arkadaşlık İsteği'
        FRIEND_ACCEPTED = 'friend_accepted', 'Arkadaşlık Kabul Edildi'
        NEW_RATING = 'new_rating', 'Yeni Puanlama'
        MOVIE_RECOMMENDATION = 'recommendation', 'Film Önerisi'
        WATCHLIST_REMINDER = 'watchlist_reminder', 'İzleme Listesi Hatırlatma'
        UPCOMING_MOVIE = 'upcoming_movie', 'Yakında Vizyona Girecek Film'
        WEEKLY_DIGEST = 'weekly_digest', 'Haftalık Özet'
        SYSTEM = 'system', 'Sistem Bildirimi'
    
    # İlişkiler
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Kullanıcı'
    )
    
    # Bildirim tipi
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
        verbose_name='Bildirim Tipi'
    )
    
    # İçerik
    title = models.CharField(max_length=200, verbose_name='Başlık')
    message = models.TextField(verbose_name='Mesaj')
    
    # İlişkili objeler (opsiyonel)
    related_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
        verbose_name='İlişkili Kullanıcı'
    )
    related_movie_id = models.IntegerField(null=True, blank=True, verbose_name='İlişkili Film ID')
    
    # URL (tıklandığında gidilecek sayfa)
    action_url = models.CharField(max_length=500, blank=True, default='', verbose_name='Aksiyon URL')
    
    # Durum
    is_read = models.BooleanField(default=False, verbose_name='Okundu mu?')
    is_email_sent = models.BooleanField(default=False, verbose_name='E-posta Gönderildi mi?')
    
    # Tarihler
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Okunma Tarihi')
    
    class Meta:
        verbose_name = 'Bildirim'
        verbose_name_plural = 'Bildirimler'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Bildirimi okundu olarak işaretle"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationPreference(models.Model):
    """Kullanıcı bildirim tercihleri"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name='Kullanıcı'
    )
    
    # E-posta bildirimleri
    email_friend_requests = models.BooleanField(default=True, verbose_name='Arkadaşlık İstekleri (E-posta)')
    email_recommendations = models.BooleanField(default=True, verbose_name='Film Önerileri (E-posta)')
    email_weekly_digest = models.BooleanField(default=True, verbose_name='Haftalık Özet (E-posta)')
    email_upcoming_movies = models.BooleanField(default=True, verbose_name='Yeni Film Bildirimleri (E-posta)')
    
    # Uygulama içi bildirimler
    push_friend_requests = models.BooleanField(default=True, verbose_name='Arkadaşlık İstekleri (Push)')
    push_friend_ratings = models.BooleanField(default=True, verbose_name='Arkadaş Puanlamaları (Push)')
    push_recommendations = models.BooleanField(default=True, verbose_name='Film Önerileri (Push)')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Bildirim Tercihi'
        verbose_name_plural = 'Bildirim Tercihleri'
    
    def __str__(self):
        return f"{self.user.username} - Bildirim Tercihleri"
