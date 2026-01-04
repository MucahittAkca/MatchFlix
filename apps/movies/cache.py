"""
Cache Utilities for MatchFlix
=============================
Film verileri için cache fonksiyonları.
"""

from django.core.cache import cache
from django.conf import settings
import hashlib


# Cache key prefixleri
CACHE_KEYS = {
    'movie_detail': 'movie:{movie_id}',
    'movie_list': 'movies:list:{page}:{filters_hash}',
    'trending': 'movies:trending:{lang}',
    'upcoming': 'movies:upcoming:{lang}',
    'user_recommendations': 'user:{user_id}:recommendations',
    'user_watchlist': 'user:{user_id}:watchlist',
    'user_ratings': 'user:{user_id}:ratings',
    'genre_list': 'genres:all',
    'tmdb_search': 'tmdb:search:{query_hash}',
}

# Cache süreleri (saniye)
CACHE_TIMEOUTS = {
    'movie_detail': 60 * 60,       # 1 saat
    'movie_list': 60 * 15,         # 15 dakika
    'trending': 60 * 60,           # 1 saat
    'upcoming': 60 * 60 * 6,       # 6 saat
    'user_recommendations': 60 * 30,  # 30 dakika
    'user_watchlist': 60 * 5,      # 5 dakika
    'user_ratings': 60 * 5,        # 5 dakika
    'genre_list': 60 * 60 * 24,    # 24 saat
    'tmdb_search': 60 * 60,        # 1 saat
}


def get_cache_key(key_type: str, **kwargs) -> str:
    """Cache key oluştur"""
    template = CACHE_KEYS.get(key_type, key_type)
    return template.format(**kwargs)


def make_filters_hash(filters: dict) -> str:
    """Filtre parametrelerinden hash oluştur"""
    sorted_items = sorted(filters.items())
    filter_str = str(sorted_items)
    return hashlib.md5(filter_str.encode()).hexdigest()[:8]


def cache_movie_detail(movie_id: int, data: dict) -> None:
    """Film detayını cache'le"""
    key = get_cache_key('movie_detail', movie_id=movie_id)
    timeout = CACHE_TIMEOUTS['movie_detail']
    cache.set(key, data, timeout)


def get_cached_movie_detail(movie_id: int):
    """Cache'den film detayı al"""
    key = get_cache_key('movie_detail', movie_id=movie_id)
    return cache.get(key)


def invalidate_movie_cache(movie_id: int) -> None:
    """Film cache'ini temizle"""
    key = get_cache_key('movie_detail', movie_id=movie_id)
    cache.delete(key)


def cache_trending_movies(movies: list, lang: str = 'tr') -> None:
    """Trending filmleri cache'le"""
    key = get_cache_key('trending', lang=lang)
    timeout = CACHE_TIMEOUTS['trending']
    cache.set(key, movies, timeout)


def get_cached_trending_movies(lang: str = 'tr'):
    """Cache'den trending filmleri al"""
    key = get_cache_key('trending', lang=lang)
    return cache.get(key)


def cache_upcoming_movies(movies: list, lang: str = 'tr') -> None:
    """Yakında vizyona girecek filmleri cache'le"""
    key = get_cache_key('upcoming', lang=lang)
    timeout = CACHE_TIMEOUTS['upcoming']
    cache.set(key, movies, timeout)


def get_cached_upcoming_movies(lang: str = 'tr'):
    """Cache'den yakında vizyona girecek filmleri al"""
    key = get_cache_key('upcoming', lang=lang)
    return cache.get(key)


def cache_user_watchlist(user_id: int, watchlist: list) -> None:
    """Kullanıcı watchlist'ini cache'le"""
    key = get_cache_key('user_watchlist', user_id=user_id)
    timeout = CACHE_TIMEOUTS['user_watchlist']
    cache.set(key, watchlist, timeout)


def get_cached_user_watchlist(user_id: int):
    """Cache'den kullanıcı watchlist'ini al"""
    key = get_cache_key('user_watchlist', user_id=user_id)
    return cache.get(key)


def invalidate_user_watchlist(user_id: int) -> None:
    """Kullanıcı watchlist cache'ini temizle"""
    key = get_cache_key('user_watchlist', user_id=user_id)
    cache.delete(key)


def cache_user_ratings(user_id: int, ratings: list) -> None:
    """Kullanıcı puanlarını cache'le"""
    key = get_cache_key('user_ratings', user_id=user_id)
    timeout = CACHE_TIMEOUTS['user_ratings']
    cache.set(key, ratings, timeout)


def get_cached_user_ratings(user_id: int):
    """Cache'den kullanıcı puanlarını al"""
    key = get_cache_key('user_ratings', user_id=user_id)
    return cache.get(key)


def invalidate_user_ratings(user_id: int) -> None:
    """Kullanıcı rating cache'ini temizle"""
    key = get_cache_key('user_ratings', user_id=user_id)
    cache.delete(key)


def cache_genre_list(genres: list) -> None:
    """Tür listesini cache'le"""
    key = get_cache_key('genre_list')
    timeout = CACHE_TIMEOUTS['genre_list']
    cache.set(key, genres, timeout)


def get_cached_genre_list():
    """Cache'den tür listesini al"""
    key = get_cache_key('genre_list')
    return cache.get(key)


def cache_tmdb_search(query: str, results: list) -> None:
    """TMDB arama sonuçlarını cache'le"""
    query_hash = hashlib.md5(query.lower().encode()).hexdigest()[:12]
    key = get_cache_key('tmdb_search', query_hash=query_hash)
    timeout = CACHE_TIMEOUTS['tmdb_search']
    cache.set(key, results, timeout)


def get_cached_tmdb_search(query: str):
    """Cache'den TMDB arama sonuçlarını al"""
    query_hash = hashlib.md5(query.lower().encode()).hexdigest()[:12]
    key = get_cache_key('tmdb_search', query_hash=query_hash)
    return cache.get(key)


def clear_all_movie_caches() -> None:
    """Tüm film cache'lerini temizle (dikkatli kullan!)"""
    # Redis kullanılıyorsa pattern ile silme yapılabilir
    # LocMemCache için bu çalışmaz
    try:
        cache.clear()
    except Exception:
        pass


# Decorator versiyonu
def cached(key_type: str, timeout: int = None):
    """
    Cache decorator
    
    Kullanım:
        @cached('movie_detail', timeout=3600)
        def get_movie(movie_id):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Cache key oluştur
            cache_key = get_cache_key(key_type, **kwargs)
            
            # Cache'de var mı?
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Yoksa hesapla
            result = func(*args, **kwargs)
            
            # Cache'e kaydet
            cache_timeout = timeout or CACHE_TIMEOUTS.get(key_type, 60 * 15)
            cache.set(cache_key, result, cache_timeout)
            
            return result
        return wrapper
    return decorator

