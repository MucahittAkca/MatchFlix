"""
Notifications App Tests
=======================
Notification ve NotificationPreference model testleri
"""

import pytest
from django.utils import timezone
from apps.notifications.models import Notification, NotificationPreference


# ============================================================================
# NOTIFICATION MODEL TESTS
# ============================================================================

class TestNotificationModel:
    """Notification modeli testleri"""
    
    @pytest.mark.django_db
    def test_create_notification(self, user, create_notification):
        """Notification oluşturma testi"""
        notification = create_notification(
            user,
            notification_type='friend_request',
            title="Arkadaşlık İsteği",
            message="Test User size arkadaşlık isteği gönderdi"
        )
        
        assert notification.user == user
        assert notification.notification_type == 'friend_request'
        assert notification.title == "Arkadaşlık İsteği"
        assert notification.is_read is False
    
    @pytest.mark.django_db
    def test_notification_str(self, notification):
        """Notification __str__ metodu"""
        assert "testuser" in str(notification)
    
    @pytest.mark.django_db
    def test_notification_types(self, user, create_notification):
        """Tüm notification tipleri test"""
        types = [
            'friend_request',
            'friend_accepted',
            'new_rating',
            'recommendation',
            'watchlist_reminder',
            'upcoming_movie',
            'weekly_digest',
            'system'
        ]
        
        for ntype in types:
            notif = create_notification(
                user,
                notification_type=ntype,
                title=f"Test {ntype}"
            )
            assert notif.notification_type == ntype
    
    @pytest.mark.django_db
    def test_mark_as_read(self, notification):
        """Bildirimi okundu olarak işaretle"""
        assert notification.is_read is False
        assert notification.read_at is None
        
        notification.mark_as_read()
        notification.refresh_from_db()
        
        assert notification.is_read is True
        assert notification.read_at is not None
    
    @pytest.mark.django_db
    def test_mark_as_read_idempotent(self, notification):
        """mark_as_read birden fazla çağrılabilir"""
        notification.mark_as_read()
        first_read_at = notification.read_at
        
        notification.mark_as_read()
        notification.refresh_from_db()
        
        # read_at değişmemeli
        assert notification.read_at == first_read_at
    
    @pytest.mark.django_db
    def test_notification_with_related_user(self, user, user2, create_notification):
        """İlişkili kullanıcı ile bildirim"""
        notification = create_notification(
            user,
            notification_type='friend_request',
            title="Arkadaşlık İsteği",
            message="Yeni istek",
            related_user=user2
        )
        
        assert notification.related_user == user2
    
    @pytest.mark.django_db
    def test_notification_with_related_movie(self, user, movie, create_notification):
        """İlişkili film ile bildirim"""
        notification = create_notification(
            user,
            notification_type='new_rating',
            title="Yeni Puanlama",
            message="Arkadaşın film puanladı",
            related_movie_id=movie.id
        )
        
        assert notification.related_movie_id == movie.id
    
    @pytest.mark.django_db
    def test_notification_ordering(self, user, create_notification):
        """Bildirimler tarihe göre sıralanır (yeni en üstte)"""
        notif1 = create_notification(user, title="First")
        notif2 = create_notification(user, title="Second")
        
        notifications = Notification.objects.filter(user=user)
        assert notifications.first() == notif2
    
    @pytest.mark.django_db
    def test_unread_notifications_filter(self, user, create_notification):
        """Okunmamış bildirimleri filtrele"""
        notif1 = create_notification(user, title="Unread 1")
        notif2 = create_notification(user, title="Unread 2")
        notif3 = create_notification(user, title="Read")
        notif3.mark_as_read()
        
        unread = Notification.objects.filter(user=user, is_read=False)
        assert unread.count() == 2


# ============================================================================
# NOTIFICATION PREFERENCE TESTS
# ============================================================================

class TestNotificationPreferenceModel:
    """NotificationPreference modeli testleri"""
    
    @pytest.mark.django_db
    def test_get_or_create_notification_preference(self, user):
        """NotificationPreference get or create"""
        # Signal zaten oluşturmuş olabilir, get_or_create kullan
        prefs, created = NotificationPreference.objects.get_or_create(user=user)
        
        assert prefs.user == user
        # Varsayılan değerler True
        assert prefs.email_friend_requests is True
        assert prefs.email_recommendations is True
        assert prefs.push_friend_requests is True
    
    @pytest.mark.django_db
    def test_preference_str(self, user):
        """NotificationPreference __str__ metodu"""
        prefs, _ = NotificationPreference.objects.get_or_create(user=user)
        assert "testuser" in str(prefs)
    
    @pytest.mark.django_db
    def test_update_preferences(self, user):
        """Tercihleri güncelle"""
        prefs, _ = NotificationPreference.objects.get_or_create(user=user)
        prefs.email_weekly_digest = False
        prefs.push_friend_ratings = False
        prefs.save()
        
        prefs.refresh_from_db()
        assert prefs.email_weekly_digest is False
        assert prefs.push_friend_ratings is False


# ============================================================================
# NOTIFICATION PAGE TESTS
# ============================================================================

class TestNotificationPages:
    """Notification sayfa testleri"""
    
    @pytest.mark.django_db
    def test_notifications_page_requires_login(self, client):
        """Bildirimler sayfası login gerektirir"""
        response = client.get('/notifications/')
        assert response.status_code == 302
    
    @pytest.mark.django_db
    def test_notifications_page_loads(self, client_with_user):
        """Bildirimler sayfası login ile yüklenir"""
        response = client_with_user.get('/notifications/')
        assert response.status_code == 200
    
    @pytest.mark.django_db
    def test_unread_count_api(self, client_with_user, user, create_notification):
        """Okunmamış bildirim sayısı API'si"""
        create_notification(user, title="Test 1")
        create_notification(user, title="Test 2")
        
        response = client_with_user.get('/notifications/api/unread-count/')
        assert response.status_code == 200
        
        data = response.json()
        assert 'unread_count' in data
        assert data['unread_count'] >= 2


# ============================================================================
# NOTIFICATION SIGNAL TESTS
# ============================================================================

class TestNotificationSignals:
    """Bildirim signal testleri"""
    
    @pytest.mark.django_db
    def test_notification_preference_created_for_new_user(self, create_user):
        """Yeni user oluşturulduğunda preference da oluşur"""
        user = create_user()
        
        # Signal tetiklenmeli
        assert NotificationPreference.objects.filter(user=user).exists()
    
    @pytest.mark.django_db
    def test_friendship_creates_notification(self, user, user2, create_friendship):
        """Arkadaşlık isteği bildirim oluşturur"""
        # Önceki bildirimleri temizle
        Notification.objects.filter(user=user2).delete()
        
        # Arkadaşlık isteği gönder
        create_friendship(user, user2, status='pending')
        
        # Bildirim oluşmuş olmalı
        notif = Notification.objects.filter(
            user=user2,
            notification_type='friend_request'
        ).first()
        
        assert notif is not None
        assert user.username in notif.message
