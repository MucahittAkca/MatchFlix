"""
Toplu Film Çekme Komutu
=======================
TMDB'den binlerce film çeker:
- Popüler filmler
- En yüksek puanlı filmler
- Tür bazlı filmler
- Yıl bazlı filmler
"""

from datetime import datetime
from django.core.management.base import BaseCommand
from apps.movies.models import Movie, Genre, Person, MovieCast, MovieCrew
from apps.movies.services import tmdb_service
import time


class Command(BaseCommand):
    help = 'TMDB\'den toplu film çeker (binlerce film)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--popular-pages',
            type=int,
            default=50,
            help='Popüler film sayfası sayısı (her sayfa 20 film)'
        )
        parser.add_argument(
            '--top-rated-pages',
            type=int,
            default=50,
            help='Top rated film sayfası sayısı'
        )
        parser.add_argument(
            '--by-genre',
            action='store_true',
            help='Her türden film çek'
        )
        parser.add_argument(
            '--genre-pages',
            type=int,
            default=10,
            help='Her tür için sayfa sayısı'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.25,
            help='API istekleri arası bekleme (saniye)'
        )

    def handle(self, *args, **options):
        total_created = 0
        total_processed = 0
        
        self.stdout.write(self.style.WARNING('\n' + '='*60))
        self.stdout.write(self.style.WARNING('TOPLU FILM CEKME ISLEMI'))
        self.stdout.write(self.style.WARNING('='*60 + '\n'))
        
        # 1. Popüler Filmler
        if options['popular_pages'] > 0:
            created = self._fetch_movies(
                'popular',
                options['popular_pages'],
                options['delay']
            )
            total_created += created
        
        # 2. Top Rated Filmler
        if options['top_rated_pages'] > 0:
            created = self._fetch_movies(
                'top_rated',
                options['top_rated_pages'],
                options['delay']
            )
            total_created += created
        
        # 3. Tür Bazlı Filmler
        if options['by_genre']:
            genres = Genre.objects.all()
            for genre in genres:
                self.stdout.write(f'\n[GENRE] {genre.name} filmleri cekiliyor...')
                created = self._fetch_by_genre(
                    genre.tmdb_id,
                    options['genre_pages'],
                    options['delay']
                )
                total_created += created
        
        # Sonuç
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(
            f'TAMAMLANDI! Toplam {total_created} yeni film eklendi.'
        ))
        self.stdout.write(f'Veritabanindaki toplam film: {Movie.objects.count()}')
        self.stdout.write('='*60 + '\n')

    def _fetch_movies(self, category, pages, delay):
        """Belirli kategoriden film çek."""
        self.stdout.write(f'\n[{category.upper()}] {pages} sayfa cekiliyor...')
        
        created_count = 0
        
        for page in range(1, pages + 1):
            try:
                if category == 'popular':
                    data = tmdb_service.get_popular_movies(page=page)
                elif category == 'top_rated':
                    data = tmdb_service.get_top_rated_movies(page=page)
                else:
                    continue
                
                movies_data = data.get('results', [])
                
                for movie_data in movies_data:
                    try:
                        # Zaten var mı kontrol et
                        if Movie.objects.filter(tmdb_id=movie_data['id']).exists():
                            continue
                        
                        # Detayları al
                        details = tmdb_service.get_movie_details(movie_data['id'])
                        movie, created = self._save_movie(details)
                        
                        if created:
                            created_count += 1
                        
                        time.sleep(delay)
                        
                    except Exception as e:
                        self.stderr.write(f'  Hata (film {movie_data.get("id")}): {e}')
                        continue
                
                # İlerleme göster
                if page % 10 == 0:
                    self.stdout.write(f'  Sayfa {page}/{pages} - {created_count} yeni film')
                    
            except Exception as e:
                self.stderr.write(f'  Sayfa {page} hatasi: {e}')
                time.sleep(1)
                continue
        
        self.stdout.write(self.style.SUCCESS(
            f'  [{category}] {created_count} yeni film eklendi'
        ))
        return created_count

    def _fetch_by_genre(self, genre_id, pages, delay):
        """Belirli türden film çek."""
        created_count = 0
        
        for page in range(1, pages + 1):
            try:
                data = tmdb_service.discover_movies(
                    genre_id=genre_id,
                    page=page,
                    sort_by='popularity.desc'
                )
                
                movies_data = data.get('results', [])
                
                for movie_data in movies_data:
                    try:
                        if Movie.objects.filter(tmdb_id=movie_data['id']).exists():
                            continue
                        
                        details = tmdb_service.get_movie_details(movie_data['id'])
                        movie, created = self._save_movie(details)
                        
                        if created:
                            created_count += 1
                        
                        time.sleep(delay)
                        
                    except Exception as e:
                        continue
                        
            except Exception as e:
                continue
        
        self.stdout.write(f'    {created_count} yeni film')
        return created_count

    def _save_movie(self, data):
        """Film verisini kaydet."""
        release_date = None
        if data.get('release_date'):
            try:
                release_date = datetime.strptime(
                    data.get('release_date'), '%Y-%m-%d'
                ).date()
            except (ValueError, TypeError):
                release_date = None
        
        movie, created = Movie.objects.update_or_create(
            tmdb_id=data['id'],
            defaults={
                'imdb_id': data.get('imdb_id'),
                'title': data.get('title', ''),
                'original_title': data.get('original_title', ''),
                'overview': data.get('overview', ''),
                'tagline': data.get('tagline', ''),
                'poster_path': data.get('poster_path'),
                'backdrop_path': data.get('backdrop_path'),
                'release_date': release_date,
                'runtime': data.get('runtime'),
                'vote_average': data.get('vote_average', 0),
                'vote_count': data.get('vote_count', 0),
                'popularity': data.get('popularity', 0),
                'original_language': data.get('original_language', 'en'),
                'status': data.get('status', 'released').lower().replace(' ', '_'),
                'adult': data.get('adult', False),
                'budget': data.get('budget', 0),
                'revenue': data.get('revenue', 0),
                'homepage': data.get('homepage'),
            }
        )

        # Türleri ekle
        if 'genres' in data:
            genre_ids = [g['id'] for g in data['genres']]
            genres = Genre.objects.filter(tmdb_id__in=genre_ids)
            movie.genres.set(genres)

        # Cast ekle (ilk 10)
        if 'credits' in data and 'cast' in data['credits']:
            for cast_data in data['credits']['cast'][:10]:
                person = self._get_or_create_person(cast_data)
                MovieCast.objects.get_or_create(
                    movie=movie,
                    person=person,
                    character_name=cast_data.get('character', ''),
                    defaults={'cast_order': cast_data.get('order', 0)},
                )

        # Yönetmen ekle
        if 'credits' in data and 'crew' in data['credits']:
            for crew_data in data['credits']['crew']:
                if crew_data.get('job') == 'Director':
                    person = self._get_or_create_person(crew_data)
                    MovieCrew.objects.get_or_create(
                        movie=movie,
                        person=person,
                        job='Director',
                        defaults={'department': 'Directing'}
                    )

        return movie, created

    def _get_or_create_person(self, data):
        """Kişi oluştur veya getir."""
        person, _ = Person.objects.get_or_create(
            tmdb_id=data['id'],
            defaults={
                'name': data.get('name', ''),
                'profile_path': data.get('profile_path'),
                'known_for_department': data.get('known_for_department', ''),
                'gender': data.get('gender', 0),
                'popularity': data.get('popularity', 0),
            }
        )
        return person

