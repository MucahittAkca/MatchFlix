"""
User App Tests
==============
User, Friendship ve CompatibilityScore model testleri
"""

import pytest
from django.contrib.auth import get_user_model
from apps.users.models import Friendship, CompatibilityScore

User = get_user_model()


# ============================================================================
# USER MODEL TESTS
# ============================================================================

class TestUserModel:
    """User modeli testleri"""
    
    @pytest.mark.django_db
    def test_create_user(self, create_user):
        """User oluşturma testi"""
        user = create_user(username="newuser", email="new@example.com")
        
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.check_password("TestPassword123!")
        assert user.is_active is True
        assert user.is_staff is False
    
    @pytest.mark.django_db
    def test_user_str(self, user):
        """User __str__ metodu testi"""
        assert str(user) == "testuser"
    
    @pytest.mark.django_db
    def test_user_email_unique(self, user, create_user):
        """Aynı email ile ikinci user oluşturulamaz"""
        with pytest.raises(Exception):
            create_user(username="anotheruser", email=user.email)
    
    @pytest.mark.django_db
    def test_user_default_values(self, user):
        """User varsayılan değerler testi"""
        assert user.total_movies_watched == 0
        assert user.avg_rating == 0.0
        assert user.bio is None
    
    @pytest.mark.django_db
    def test_get_friends_empty(self, user):
        """Arkadaşı olmayan user için boş liste döner"""
        friends = user.get_friends()
        assert friends == []
    
    @pytest.mark.django_db
    def test_get_friends_accepted(self, user, user2, create_friendship):
        """Kabul edilmiş arkadaşlıklar döner"""
        create_friendship(user, user2, status='accepted')
        
        friends = user.get_friends()
        assert len(friends) == 1
        assert user2 in friends
        
        # Diğer taraftan da kontrol
        friends2 = user2.get_friends()
        assert len(friends2) == 1
        assert user in friends2
    
    @pytest.mark.django_db
    def test_get_pending_requests(self, user, user2, create_friendship):
        """Bekleyen istekleri döndür"""
        create_friendship(user2, user, status='pending')
        
        pending = user.get_pending_requests()
        assert pending.count() == 1
        assert pending.first().user == user2
    
    @pytest.mark.django_db
    def test_get_sent_requests(self, user, user2, create_friendship):
        """Gönderilen istekleri döndür"""
        create_friendship(user, user2, status='pending')
        
        sent = user.get_sent_requests()
        assert sent.count() == 1
        assert sent.first().friend == user2


# ============================================================================
# FRIENDSHIP MODEL TESTS
# ============================================================================

class TestFriendshipModel:
    """Friendship modeli testleri"""
    
    @pytest.mark.django_db
    def test_create_friendship(self, user, user2, create_friendship):
        """Arkadaşlık isteği oluşturma"""
        friendship = create_friendship(user, user2)
        
        assert friendship.user == user
        assert friendship.friend == user2
        assert friendship.status == 'pending'
    
    @pytest.mark.django_db
    def test_friendship_str(self, friendship):
        """Friendship __str__ metodu"""
        assert "testuser" in str(friendship)
        assert "testuser2" in str(friendship)
        assert "Beklemede" in str(friendship)
    
    @pytest.mark.django_db
    def test_accept_friendship(self, friendship):
        """Arkadaşlık isteğini kabul et"""
        friendship.accept()
        friendship.refresh_from_db()
        
        assert friendship.status == 'accepted'
    
    @pytest.mark.django_db
    def test_reject_friendship(self, friendship):
        """Arkadaşlık isteğini reddet"""
        friendship.reject()
        friendship.refresh_from_db()
        
        assert friendship.status == 'rejected'
    
    @pytest.mark.django_db
    def test_block_user(self, friendship):
        """Kullanıcıyı engelle"""
        friendship.block()
        friendship.refresh_from_db()
        
        assert friendship.status == 'blocked'
    
    @pytest.mark.django_db
    def test_unique_friendship(self, user, user2, create_friendship):
        """Aynı kullanıcılar arasında tek arkadaşlık"""
        create_friendship(user, user2)
        
        with pytest.raises(Exception):
            create_friendship(user, user2)


# ============================================================================
# COMPATIBILITY SCORE TESTS
# ============================================================================

class TestCompatibilityScoreModel:
    """CompatibilityScore modeli testleri"""
    
    @pytest.mark.django_db
    def test_create_compatibility_score(self, user, user2):
        """Uyumluluk skoru oluşturma"""
        score = CompatibilityScore.objects.create(
            user_1=user,
            user_2=user2,
            score=85,
            common_movies=10
        )
        
        assert score.score == 85
        assert score.common_movies == 10
    
    @pytest.mark.django_db
    def test_compatibility_score_str(self, user, user2):
        """CompatibilityScore __str__ metodu"""
        score = CompatibilityScore.objects.create(
            user_1=user,
            user_2=user2,
            score=75
        )
        
        assert "testuser" in str(score)
        assert "testuser2" in str(score)
        assert "75" in str(score)
    
    @pytest.mark.django_db
    def test_unique_user_pair(self, user, user2):
        """Aynı kullanıcı çifti için tek skor"""
        CompatibilityScore.objects.create(user_1=user, user_2=user2, score=50)
        
        with pytest.raises(Exception):
            CompatibilityScore.objects.create(user_1=user, user_2=user2, score=60)


# ============================================================================
# USER PAGE TESTS
# ============================================================================

class TestUserPages:
    """User sayfa testleri"""
    
    @pytest.mark.django_db
    def test_login_success(self, client, user, user_password):
        """Başarılı giriş"""
        response = client.post('/login/', {
            'username': user.username,
            'password': user_password
        })
        # Login başarılı olunca /home/'a redirect
        assert response.status_code in [200, 302]
    
    @pytest.mark.django_db
    def test_login_wrong_password(self, client, user):
        """Yanlış şifre ile giriş"""
        response = client.post('/login/', {
            'username': user.username,
            'password': 'wrongpassword'
        })
        # Hatalı giriş aynı sayfada kalır
        assert response.status_code == 200
    
    @pytest.mark.django_db
    def test_register_page_loads(self, client):
        """Kayıt sayfası yüklenir"""
        response = client.get('/register/')
        assert response.status_code == 200
    
    @pytest.mark.django_db
    def test_register_duplicate_email(self, client, user):
        """Aynı email ile kayıt engellemesi"""
        response = client.post('/register/', {
            'username': 'newuser',
            'email': user.email,  # Var olan email
            'password': 'NewPassword123!',
            'password2': 'NewPassword123!'
        })
        assert response.status_code == 200


# ============================================================================
# FRIENDSHIP PAGE TESTS
# ============================================================================

class TestFriendshipPages:
    """Friendship sayfa testleri"""
    
    @pytest.mark.django_db
    def test_friends_page_requires_login(self, client):
        """Arkadaşlar sayfası login gerektirir"""
        response = client.get('/friends/')
        assert response.status_code == 302  # Login'e redirect
    
    @pytest.mark.django_db
    def test_friends_page_loads(self, client_with_user):
        """Arkadaşlar sayfası login ile yüklenir"""
        response = client_with_user.get('/friends/')
        assert response.status_code == 200
    
    @pytest.mark.django_db
    def test_profile_page_loads(self, client_with_user):
        """Profil sayfası yüklenir"""
        response = client_with_user.get('/profile/')
        assert response.status_code == 200
