"""
Movies App Tests
================
Movie, Genre, Rating, Watchlist model testleri
"""

import pytest
from datetime import date
from apps.movies.models import Movie, Genre, Rating, Watchlist, Person, MovieCast, MovieCrew


# ============================================================================
# GENRE MODEL TESTS
# ============================================================================

class TestGenreModel:
    """Genre modeli testleri"""
    
    @pytest.mark.django_db
    def test_create_genre(self):
        """Genre oluşturma testi"""
        genre = Genre.objects.create(tmdb_id=28, name="Action", name_tr="Aksiyon")
        
        assert genre.tmdb_id == 28
        assert genre.name == "Action"
        assert genre.name_tr == "Aksiyon"
    
    @pytest.mark.django_db
    def test_genre_str_with_turkish(self):
        """Türkçe isim varsa onu göster"""
        genre = Genre.objects.create(tmdb_id=29, name="Action", name_tr="Aksiyon")
        assert str(genre) == "Aksiyon"
    
    @pytest.mark.django_db
    def test_genre_str_without_turkish(self):
        """Türkçe isim yoksa İngilizce göster"""
        genre = Genre.objects.create(tmdb_id=30, name="Horror", name_tr=None)
        assert str(genre) == "Horror"
    
    @pytest.mark.django_db
    def test_genre_unique_tmdb_id(self):
        """tmdb_id benzersiz olmalı"""
        Genre.objects.create(tmdb_id=31, name="Drama")
        
        with pytest.raises(Exception):
            Genre.objects.create(tmdb_id=31, name="Comedy")


# ============================================================================
# MOVIE MODEL TESTS
# ============================================================================

class TestMovieModel:
    """Movie modeli testleri"""
    
    @pytest.mark.django_db
    def test_create_movie(self, create_movie):
        """Movie oluşturma testi"""
        movie = create_movie(
            tmdb_id=12345,
            title="Test Film",
            release_date=date(2024, 6, 15)
        )
        
        assert movie.tmdb_id == 12345
        assert movie.title == "Test Film"
        assert movie.release_date == date(2024, 6, 15)
    
    @pytest.mark.django_db
    def test_movie_str(self, movie):
        """Movie __str__ metodu"""
        assert "Test Film" in str(movie)
        assert "2024" in str(movie)
    
    @pytest.mark.django_db
    def test_movie_poster_url_with_path(self, create_movie):
        """Poster path varsa URL döner"""
        movie = create_movie(poster_path="/abc123.jpg", release_date=date(2024, 1, 1))
        assert movie.poster_url == "https://image.tmdb.org/t/p/w500/abc123.jpg"
    
    @pytest.mark.django_db
    def test_movie_poster_url_without_path(self, create_movie):
        """Poster path yoksa placeholder döner"""
        movie = create_movie(poster_path=None, release_date=date(2024, 1, 1))
        assert "placeholder" in movie.poster_url
    
    @pytest.mark.django_db
    def test_movie_backdrop_url_with_path(self, create_movie):
        """Backdrop path varsa URL döner"""
        movie = create_movie(backdrop_path="/backdrop123.jpg", release_date=date(2024, 1, 1))
        assert movie.backdrop_url == "https://image.tmdb.org/t/p/original/backdrop123.jpg"
    
    @pytest.mark.django_db
    def test_movie_backdrop_url_fallback_to_poster(self, create_movie):
        """Backdrop yoksa poster kullan"""
        movie = create_movie(backdrop_path=None, poster_path="/poster.jpg", release_date=date(2024, 1, 1))
        assert "poster.jpg" in movie.backdrop_url
    
    @pytest.mark.django_db
    def test_movie_backdrop_url_placeholder(self, create_movie):
        """Her ikisi de yoksa placeholder"""
        movie = create_movie(backdrop_path=None, poster_path=None, release_date=date(2024, 1, 1))
        assert "placeholder" in movie.backdrop_url
    
    @pytest.mark.django_db
    def test_movie_year_property(self, movie):
        """Year property testi"""
        assert movie.year == 2024
    
    @pytest.mark.django_db
    def test_movie_year_none(self, create_movie):
        """Release date yoksa year None"""
        movie = create_movie(release_date=None)
        assert movie.year is None
    
    @pytest.mark.django_db
    def test_movie_genres_relationship(self, movie, genre):
        """Movie-Genre ilişkisi"""
        assert genre in movie.genres.all()


# ============================================================================
# PERSON MODEL TESTS
# ============================================================================

class TestPersonModel:
    """Person modeli testleri"""
    
    @pytest.mark.django_db
    def test_create_person(self, db):
        """Person oluşturma testi"""
        person = Person.objects.create(
            tmdb_id=12345,
            name="Tom Hanks",
            known_for_department="Acting"
        )
        
        assert person.name == "Tom Hanks"
        assert str(person) == "Tom Hanks"
    
    @pytest.mark.django_db
    def test_person_profile_url(self, db):
        """Profile URL testi"""
        person = Person.objects.create(
            tmdb_id=123,
            name="Test Actor",
            profile_path="/profile.jpg"
        )
        
        assert person.profile_url == "https://image.tmdb.org/t/p/w185/profile.jpg"
    
    @pytest.mark.django_db
    def test_person_profile_url_none(self, db):
        """Profile path yoksa None"""
        person = Person.objects.create(tmdb_id=456, name="No Photo")
        assert person.profile_url is None


# ============================================================================
# RATING MODEL TESTS
# ============================================================================

class TestRatingModel:
    """Rating modeli testleri"""
    
    @pytest.mark.django_db
    def test_create_rating(self, user, movie, create_rating):
        """Rating oluşturma testi"""
        rating = create_rating(user, movie, score=8, review="Güzel film")
        
        assert rating.user == user
        assert rating.movie == movie
        assert rating.score == 8
        assert rating.review == "Güzel film"
    
    @pytest.mark.django_db
    def test_rating_str(self, rating):
        """Rating __str__ metodu"""
        assert "testuser" in str(rating)
        assert "Test Film" in str(rating)
        assert "9/10" in str(rating)
    
    @pytest.mark.django_db
    def test_rating_unique_user_movie(self, user, movie, create_rating):
        """Bir user bir filme tek puan verebilir"""
        create_rating(user, movie, score=7)
        
        with pytest.raises(Exception):
            create_rating(user, movie, score=9)
    
    @pytest.mark.django_db
    def test_multiple_users_can_rate_same_movie(self, user, user2, movie, create_rating):
        """Farklı userlar aynı filme puan verebilir"""
        rating1 = create_rating(user, movie, score=8)
        rating2 = create_rating(user2, movie, score=6)
        
        assert rating1.score == 8
        assert rating2.score == 6
        assert movie.ratings.count() == 2


# ============================================================================
# WATCHLIST MODEL TESTS
# ============================================================================

class TestWatchlistModel:
    """Watchlist modeli testleri"""
    
    @pytest.mark.django_db
    def test_create_watchlist_item(self, user, movie, create_watchlist):
        """Watchlist item oluşturma"""
        item = create_watchlist(user, movie)
        
        assert item.user == user
        assert item.movie == movie
    
    @pytest.mark.django_db
    def test_watchlist_str(self, watchlist_item):
        """Watchlist __str__ metodu"""
        assert "testuser" in str(watchlist_item)
        assert "Test Film" in str(watchlist_item)
    
    @pytest.mark.django_db
    def test_watchlist_unique_user_movie(self, user, movie, create_watchlist):
        """Bir film watchlist'e bir kez eklenir"""
        create_watchlist(user, movie)
        
        with pytest.raises(Exception):
            create_watchlist(user, movie)


# ============================================================================
# MOVIE CAST/CREW TESTS
# ============================================================================

class TestMovieCastCrewModel:
    """MovieCast ve MovieCrew testleri"""
    
    @pytest.mark.django_db
    def test_create_movie_cast(self, movie, db):
        """MovieCast oluşturma"""
        person = Person.objects.create(tmdb_id=111, name="Actor Name")
        cast = MovieCast.objects.create(
            movie=movie,
            person=person,
            character_name="Hero",
            cast_order=1
        )
        
        assert cast.movie == movie
        assert cast.person == person
        assert cast.character_name == "Hero"
    
    @pytest.mark.django_db
    def test_create_movie_crew(self, movie, db):
        """MovieCrew oluşturma"""
        person = Person.objects.create(tmdb_id=222, name="Director Name")
        crew = MovieCrew.objects.create(
            movie=movie,
            person=person,
            job="Director",
            department="Directing"
        )
        
        assert crew.movie == movie
        assert crew.job == "Director"


# ============================================================================
# MOVIE PAGE TESTS
# ============================================================================

class TestMoviePages:
    """Movie sayfa testleri"""
    
    @pytest.mark.django_db
    def test_home_page_loads(self, client_with_user):
        """Ana sayfa yüklenir"""
        response = client_with_user.get('/home/')
        assert response.status_code == 200
    
    @pytest.mark.django_db
    def test_movie_detail_page(self, client_with_user, movie):
        """Film detay sayfası"""
        response = client_with_user.get(f'/movie/{movie.id}/')
        assert response.status_code == 200
    
    @pytest.mark.django_db
    def test_explore_page(self, client_with_user):
        """Keşfet sayfası"""
        response = client_with_user.get('/explore/')
        assert response.status_code == 200
    
    @pytest.mark.django_db
    def test_watchlist_page(self, client_with_user):
        """İzleme listesi sayfası"""
        response = client_with_user.get('/watchlist/')
        assert response.status_code == 200


# ============================================================================
# MOVIE SERVICE TESTS
# ============================================================================

class TestMovieService:
    """TMDBService testleri"""
    
    @pytest.mark.django_db
    def test_movie_ordering(self, create_movie):
        """Filmler popülerliğe göre sıralanır"""
        movie1 = create_movie(title="Less Popular", popularity=10, release_date=date(2024, 1, 1))
        movie2 = create_movie(title="More Popular", popularity=100, release_date=date(2024, 1, 1))
        
        movies = Movie.objects.all()
        assert movies.first().popularity >= movies.last().popularity
