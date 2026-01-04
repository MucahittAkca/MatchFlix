import time
import requests
from django.conf import settings
from typing import Optional, Dict, List

class TMDBService:
    """TMDB API ile iletişim"""

    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p"


    def __init__(self):
        self.api_key = settings.TMDB_API_KEY
        if not self.api_key:
            raise ValueError("TMDB_API_KEY ayarlanmamış!")
        

    def _make_request(self, endpoint: str, params: Optional[Dict] = None, language: str = 'tr-TR') -> Dict:
        """TMDB API'ye istek at."""
        if params is None:
            params = {}

        params['api_key'] = self.api_key
        params['language'] = language

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = requests.get(url, params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"TMDB API Error: {e}")
            return {}
    
    def _is_non_latin(self, text: str) -> bool:
        """Metnin Latin olmayan karakterler içerip içermediğini kontrol et"""
        if not text:
            return False
        # Latin harfleri ve yaygın karakterler
        latin_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-:;\'"()[]{}@#$%&*+=/<>~`')
        non_latin_count = sum(1 for char in text if char not in latin_chars)
        return non_latin_count > len(text) * 0.3  # %30'dan fazla non-Latin ise
    
    def get_movie_with_fallback(self, tmdb_id: int) -> Dict:
        """Film detaylarını getir, Türkçe yoksa İngilizce'ye düş"""
        # Önce Türkçe dene
        movie_data = self._make_request(f'movie/{tmdb_id}', {
            'append_to_response': 'credits,videos,images'
        }, language='tr-TR')
        
        if not movie_data:
            return {}
        
        # Başlık non-Latin veya overview boşsa İngilizce'ye düş
        title = movie_data.get('title', '')
        overview = movie_data.get('overview', '')
        
        if self._is_non_latin(title) or not overview:
            en_data = self._make_request(f'movie/{tmdb_id}', {
                'append_to_response': 'credits,videos,images'
            }, language='en-US')
            
            if en_data:
                # İngilizce başlık ve overview kullan (Türkçe yoksa)
                if self._is_non_latin(title) or not title:
                    movie_data['title'] = en_data.get('title', title)
                if not overview:
                    movie_data['overview'] = en_data.get('overview', '')
                # Tagline de kontrol et
                if not movie_data.get('tagline'):
                    movie_data['tagline'] = en_data.get('tagline', '')
        
        return movie_data
        

    def search_movie(self, query: str, page: int = 1) -> Dict:
        """Film ara"""
        return self._make_request('search/movie', {
            'query': query,
            'page': page,
            'include_adult': False
        })
    
    def get_movie_details(self, tmdb_id: int) -> Dict:
        """Film detaylarını getir."""
        return self._make_request(f'movie/{tmdb_id}', {
            'append_to_response': 'credits, videos, images'
        })
    
    def get_popular_movies(self, page: int = 1) -> Dict:
        """Popüler filmleri getir."""
        return self._make_request('movie/popular', {'page': page})
    
    def get_trending_movies(self, time_window: str = 'week') -> Dict:
        """Trend filmleri getir."""
        return self._make_request(f'trending/movie/{time_window}')
    
    def get_upcoming_movies(self, page: int = 1) -> Dict:
        """Vizyona girecek filmler"""
        return self._make_request('movie/upcoming', {
            'page': page,
            'region': 'TR'
        })
    
    def get_top_rated_movies(self, page: int = 1) -> Dict:
        """En iyi değerlendirilen filmleri getir."""
        return self._make_request('movie/top_rated', {'page': page})
    
    def get_genres(self) -> List[Dict]:
        """Tür listesini getir."""
        data = self._make_request('genre/movie/list')
        return data.get('genres', [])
    
    def get_person_details(self, person_id: int) -> Dict:
        """Kişi detaylarını getir."""
        return self._make_request(f'person/{person_id}')
    
    def discover_movies(self, page: int = 1, genre_id: int = None, year: int = None, 
                        vote_average_gte: float = None, sort_by: str = 'popularity.desc') -> Dict:
        """Filtrelere göre film keşfet (TMDB Discover API)"""
        params = {
            'page': page,
            'sort_by': sort_by,
            'include_adult': False,
            'include_video': False,
        }
        
        if genre_id:
            params['with_genres'] = genre_id
        
        if year:
            params['primary_release_year'] = year
        
        if vote_average_gte and vote_average_gte > 0:
            params['vote_average.gte'] = vote_average_gte
            params['vote_count.gte'] = 50  # En az 50 oy almış filmler
        
        return self._make_request('discover/movie', params)
    
    def get_watch_providers(self, tmdb_id: int, country: str = 'TR') -> Dict:
        """
        Film için izleme platformlarını getir (JustWatch verisi)
        
        Returns:
            {
                'flatrate': [...],  # Abonelikle izlenebilir (Netflix, Disney+ vs.)
                'rent': [...],      # Kiralık
                'buy': [...],       # Satın alınabilir
                'link': '...'       # JustWatch linki
            }
        """
        data = self._make_request(f'movie/{tmdb_id}/watch/providers')
        
        if not data or 'results' not in data:
            return {}
        
        # Ülkeye göre filtrele (varsayılan Türkiye)
        country_data = data.get('results', {}).get(country, {})
        
        if not country_data:
            # Türkiye'de yoksa US dene
            country_data = data.get('results', {}).get('US', {})
        
        return {
            'flatrate': country_data.get('flatrate', []),  # Abonelik platformları
            'rent': country_data.get('rent', []),          # Kiralık
            'buy': country_data.get('buy', []),            # Satın alma
            'link': country_data.get('link', ''),          # JustWatch linki
        }
    
    def get_available_providers(self) -> List[Dict]:
        """Türkiye'de mevcut izleme platformlarını getir"""
        data = self._make_request('watch/providers/movie', {'watch_region': 'TR'})
        return data.get('results', [])

tmdb_service = TMDBService()