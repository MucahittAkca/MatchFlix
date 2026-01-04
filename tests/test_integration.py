"""
Integration Tests
=================
Uçtan uca entegrasyon testleri
"""

import pytest
from django.contrib.auth import get_user_model
from apps.movies.models import Movie, Rating, Watchlist
from apps.users.models import Friendship
from apps.notifications.models import Notification

User = get_user_model()


class TestUserJourney:
    """Kullanıcı yolculuğu entegrasyon testleri"""
    
    @pytest.mark.django_db
    def test_complete_user_registration_flow(self, client):
        """Kayıt -> Giriş -> Profil akışı"""
        # 1. Kayıt ol
        response = client.post('/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password2': 'SecurePass123!'
        })
        
        # User oluşturulmuş olmalı
        assert User.objects.filter(username='newuser').exists()
        
        # 2. Giriş yap
        response = client.post('/login/', {
            'username': 'newuser',
            'password': 'SecurePass123!'
        })
        assert response.status_code in [200, 302]
        
        # 3. Profil sayfasına git
        response = client.get('/profile/')
        assert response.status_code == 200


class TestMovieRatingFlow:
    """Film puanlama akış testleri"""
    
    @pytest.mark.django_db
    def test_rate_movie_flow(self, client_with_user, user, movie):
        """Film görüntüle -> Puan ver akışı"""
        # 1. Film detayına git
        response = client_with_user.get(f'/movie/{movie.id}/')
        assert response.status_code == 200
        
        # 2. Puan ver (doğrudan model ile)
        rating = Rating.objects.create(user=user, movie=movie, score=8, review="Güzel!")
        assert rating.score == 8


class TestWatchlistFlow:
    """İzleme listesi akış testleri"""
    
    @pytest.mark.django_db
    def test_add_remove_watchlist_flow(self, client_with_user, user, movie):
        """Watchlist'e ekle -> Kaldır akışı"""
        # 1. Watchlist'e ekle
        Watchlist.objects.create(user=user, movie=movie)
        assert Watchlist.objects.filter(user=user, movie=movie).exists()
        
        # 2. Watchlist sayfasını kontrol et
        response = client_with_user.get('/watchlist/')
        assert response.status_code == 200
        
        # 3. Kaldır
        Watchlist.objects.filter(user=user, movie=movie).delete()
        assert not Watchlist.objects.filter(user=user, movie=movie).exists()


class TestFriendshipFlow:
    """Arkadaşlık akış testleri"""
    
    @pytest.mark.django_db
    def test_friend_request_flow(self, user, user2, create_friendship):
        """İstek gönder -> Kabul et -> Arkadaş ol akışı"""
        # 1. Arkadaşlık isteği gönder
        friendship = create_friendship(user, user2, status='pending')
        
        # Bildirim oluşmuş olmalı
        notif = Notification.objects.filter(
            user=user2,
            notification_type='friend_request'
        ).first()
        assert notif is not None
        
        # 2. İsteği kabul et
        friendship.accept()
        friendship.refresh_from_db()
        assert friendship.status == 'accepted'
        
        # 3. Artık arkadaşlar
        assert user2 in user.get_friends()
        assert user in user2.get_friends()


class TestNotificationFlow:
    """Bildirim akış testleri"""
    
    @pytest.mark.django_db
    def test_notification_read_flow(self, client_with_user, user, create_notification):
        """Bildirim al -> Oku -> Sil akışı"""
        # 1. Bildirim oluştur
        notif = create_notification(user, title="Test Bildirim")
        
        # 2. Okunmamış sayısı kontrol
        unread = Notification.objects.filter(user=user, is_read=False).count()
        assert unread >= 1
        
        # 3. Okundu işaretle
        notif.mark_as_read()
        
        # 4. Sil
        notif.delete()
        assert not Notification.objects.filter(id=notif.id).exists()


class TestExploreFlow:
    """Keşfet akış testleri"""
    
    @pytest.mark.django_db
    def test_explore_page_flow(self, client_with_user):
        """Keşfet sayfasını ziyaret et"""
        response = client_with_user.get('/explore/')
        assert response.status_code == 200


class TestSecurityFlow:
    """Güvenlik testleri"""
    
    @pytest.mark.django_db
    def test_protected_pages_require_login(self, client):
        """Korumalı sayfalar login gerektirir"""
        protected_urls = [
            '/home/',
            '/profile/',
            '/watchlist/',
            '/friends/',
            '/notifications/',
        ]
        
        for url in protected_urls:
            response = client.get(url)
            # Login sayfasına redirect
            assert response.status_code == 302, f"{url} should require login"
    
    @pytest.mark.django_db
    def test_logout_clears_session(self, client_with_user):
        """Çıkış yapınca session temizlenir"""
        # Önce giriş yapmış
        response = client_with_user.get('/profile/')
        assert response.status_code == 200
        
        # Çıkış yap
        response = client_with_user.get('/logout/')
        
        # Artık protected sayfalara gidemez
        response = client_with_user.get('/profile/')
        assert response.status_code == 302


class TestDataIntegrity:
    """Veri bütünlüğü testleri"""
    
    @pytest.mark.django_db
    def test_user_deletion_cascades(self, user, movie, create_rating, create_watchlist):
        """User silinince ilişkili veriler de silinir"""
        user_id = user.id
        
        # Rating ve watchlist oluştur
        create_rating(user, movie)
        create_watchlist(user, movie)
        
        # User'ı sil
        user.delete()
        
        # İlişkili veriler de silinmeli
        assert not Rating.objects.filter(user_id=user_id).exists()
        assert not Watchlist.objects.filter(user_id=user_id).exists()
    
    @pytest.mark.django_db
    def test_movie_deletion_cascades(self, user, movie, create_rating, create_watchlist):
        """Movie silinince ilişkili veriler de silinir"""
        movie_id = movie.id
        
        # Rating ve watchlist oluştur
        create_rating(user, movie)
        create_watchlist(user, movie)
        
        # Movie'yi sil
        movie.delete()
        
        # İlişkili veriler de silinmeli
        assert not Rating.objects.filter(movie_id=movie_id).exists()
        assert not Watchlist.objects.filter(movie_id=movie_id).exists()
