"""
MatchFlix Test Configuration
============================
Pytest fixtures ve factory'ler
"""

import pytest
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()


# ============================================================================
# USER FIXTURES
# ============================================================================

@pytest.fixture
def user_password():
    """Test kullanıcısı için şifre"""
    return "TestPassword123!"


@pytest.fixture
def create_user(db, user_password):
    """User oluşturmak için factory fixture"""
    def _create_user(
        username=None,
        email=None,
        password=None,
        **kwargs
    ):
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        
        return User.objects.create_user(
            username=username or f"testuser_{unique_id}",
            email=email or f"test_{unique_id}@example.com",
            password=password or user_password,
            **kwargs
        )
    return _create_user


@pytest.fixture
def user(create_user):
    """Tek bir test kullanıcısı"""
    return create_user(username="testuser", email="testuser@example.com")


@pytest.fixture
def user2(create_user):
    """İkinci test kullanıcısı"""
    return create_user(username="testuser2", email="testuser2@example.com")


@pytest.fixture
def user3(create_user):
    """Üçüncü test kullanıcısı"""
    return create_user(username="testuser3", email="testuser3@example.com")


# ============================================================================
# MOVIE FIXTURES
# ============================================================================

@pytest.fixture
def create_genre(db):
    """Genre oluşturmak için factory fixture"""
    from apps.movies.models import Genre
    
    def _create_genre(tmdb_id=None, name=None, name_tr=None):
        import random
        return Genre.objects.create(
            tmdb_id=tmdb_id or random.randint(1, 99999),
            name=name or "Action",
            name_tr=name_tr
        )
    return _create_genre


@pytest.fixture
def genre(create_genre):
    """Tek bir tür"""
    return create_genre(tmdb_id=28, name="Action", name_tr="Aksiyon")


@pytest.fixture
def create_movie(db, genre):
    """Movie oluşturmak için factory fixture"""
    from apps.movies.models import Movie
    
    def _create_movie(
        tmdb_id=None,
        title=None,
        original_title=None,
        release_date=None,
        popularity=100.0,
        **kwargs
    ):
        import random
        movie = Movie.objects.create(
            tmdb_id=tmdb_id or random.randint(1, 999999),
            title=title or "Test Movie",
            original_title=original_title or title or "Test Movie",
            release_date=release_date,  # None olabilir
            original_language="en",
            vote_average=7.5,
            vote_count=1000,
            popularity=popularity,
            **kwargs
        )
        movie.genres.add(genre)
        return movie
    return _create_movie


@pytest.fixture
def movie(create_movie):
    """Tek bir film"""
    return create_movie(tmdb_id=12345, title="Test Film", release_date=date(2024, 1, 1))


@pytest.fixture
def movie2(create_movie):
    """İkinci film"""
    return create_movie(tmdb_id=12346, title="Test Film 2", release_date=date(2024, 1, 1))


# ============================================================================
# FRIENDSHIP FIXTURES
# ============================================================================

@pytest.fixture
def create_friendship(db):
    """Friendship oluşturmak için factory fixture"""
    from apps.users.models import Friendship
    
    def _create_friendship(user, friend, status='pending'):
        return Friendship.objects.create(
            user=user,
            friend=friend,
            status=status
        )
    return _create_friendship


@pytest.fixture
def friendship(create_friendship, user, user2):
    """User'dan user2'ye arkadaşlık isteği"""
    return create_friendship(user, user2, 'pending')


# ============================================================================
# RATING FIXTURES
# ============================================================================

@pytest.fixture
def create_rating(db):
    """Rating oluşturmak için factory fixture"""
    from apps.movies.models import Rating
    
    def _create_rating(user, movie, score=8, review=None):
        return Rating.objects.create(
            user=user,
            movie=movie,
            score=score,
            review=review
        )
    return _create_rating


@pytest.fixture
def rating(create_rating, user, movie):
    """User'ın filme verdiği puan"""
    return create_rating(user, movie, score=9, review="Harika film!")


# ============================================================================
# WATCHLIST FIXTURES
# ============================================================================

@pytest.fixture
def create_watchlist(db):
    """Watchlist oluşturmak için factory fixture"""
    from apps.movies.models import Watchlist
    
    def _create_watchlist(user, movie):
        return Watchlist.objects.create(user=user, movie=movie)
    return _create_watchlist


@pytest.fixture
def watchlist_item(create_watchlist, user, movie):
    """User'ın izleme listesindeki film"""
    return create_watchlist(user, movie)


# ============================================================================
# NOTIFICATION FIXTURES
# ============================================================================

@pytest.fixture
def create_notification(db):
    """Notification oluşturmak için factory fixture"""
    from apps.notifications.models import Notification
    
    def _create_notification(
        user,
        notification_type='system',
        title="Test Bildirimi",
        message="Test mesajı",
        **kwargs
    ):
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            **kwargs
        )
    return _create_notification


@pytest.fixture
def notification(create_notification, user):
    """User için bir bildirim"""
    return create_notification(user, title="Test", message="Test mesaj")


# ============================================================================
# API CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def api_client():
    """REST Framework test client"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user, user_password):
    """Giriş yapmış API client"""
    api_client.login(username=user.username, password=user_password)
    return api_client


@pytest.fixture
def client_with_user(client, user, user_password):
    """Django test client ile giriş yapmış user"""
    client.login(username=user.username, password=user_password)
    return client

