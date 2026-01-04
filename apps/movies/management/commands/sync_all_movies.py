from datetime import datetime
from django.core.management.base import BaseCommand
from apps.movies.models import Movie, Genre, Person, MovieCast, MovieCrew
from apps.movies.services import tmdb_service


class Command(BaseCommand):
    help = 'TMDB\'den popüler, trend ve en iyi değerlendirilen filmler çeker.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pages',
            type=int,
            default=5,
            help='Her kategori için kaç sayfa çekilecek (her sayfa 20 film)'
        )
        parser.add_argument(
            '--category',
            type=str,
            default='all',
            choices=['popular', 'trending', 'upcoming', 'top_rated', 'all'],
            help='Hangi kategori çekilecek'
        )


    def handle(self, *args, **options):
        pages = options['pages']
        category = options['category']
        total_created = 0

        categories = []
        
        if category == 'all':
            categories = [
                ('popular', self._fetch_popular),
                ('trending', self._fetch_trending),
                ('upcoming', self._fetch_upcoming),
                ('top_rated', self._fetch_top_rated),
            ]
        else:
            if category == 'popular':
                categories = [('popular', self._fetch_popular)]
            elif category == 'trending':
                categories = [('trending', self._fetch_trending)]
            elif category == 'upcoming':
                categories = [('upcoming', self._fetch_upcoming)]
            elif category == 'top_rated':
                categories = [('top_rated', self._fetch_top_rated)]

        for cat_name, fetch_func in categories:
            self.stdout.write(f'\n📽️ {cat_name.upper()} kategorisinden filmler çekiliyor...\n')
            created = self._process_category(fetch_func, pages)
            total_created += created
            self.stdout.write(self.style.SUCCESS(f'  → {cat_name.capitalize()}: {created} film eklendi'))

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Toplam {total_created} yeni film eklendi!')
        )

    def _process_category(self, fetch_func, pages):
        """Bir kategori için filmleri işle."""
        created_count = 0

        for page in range(1, pages + 1):
            data = fetch_func(page)
            movies_data = data.get('results', [])

            if not movies_data:
                break

            for movie_data in movies_data:
                # Film detaylarını al
                details = tmdb_service.get_movie_details(movie_data['id'])

                # Filmi kaydet
                movie, created = self._save_movie(details)

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ {movie.title} ({movie.year})')
                    )

        return created_count

    def _fetch_popular(self, page):
        """Popüler filmleri fetch et."""
        return tmdb_service.get_popular_movies(page=page)

    def _fetch_trending(self, page):
        """Trend filmleri fetch et."""
        return tmdb_service.get_trending_movies(time_window='week')

    def _fetch_upcoming(self, page):
        """Vizyona girecek filmler fetch et."""
        return tmdb_service.get_upcoming_movies(page=page)

    def _fetch_top_rated(self, page):
        """En iyi değerlendirilen filmleri fetch et."""
        return tmdb_service.get_top_rated_movies(page=page)

    def _save_movie(self, data):
        """Film verisini kaydet."""
        # release_date'i parse et
        release_date = None
        if data.get('release_date'):
            try:
                release_date = datetime.strptime(data.get('release_date'), '%Y-%m-%d').date()
            except (ValueError, TypeError):
                release_date = None
        
        # Film oluştur/güncelle
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

        # Cast ekle
        if 'credits' in data and 'cast' in data['credits']:
            for cast_data in data['credits']['cast'][:10]:
                person = self._get_or_create_person(cast_data)
                MovieCast.objects.get_or_create(
                    movie=movie,
                    person=person,
                    character_name=cast_data.get('character', ''),
                    defaults={'cast_order': cast_data.get('order', 0)},
                )

        # Ekip ekle
        if 'credits' in data and 'crew' in data['credits']:
            for crew_data in data['credits']['crew']:
                if crew_data.get('department') in ['Directing', 'Writing']:
                    person = self._get_or_create_person(crew_data)
                    MovieCrew.objects.get_or_create(
                        movie=movie,
                        person=person,
                        department=crew_data.get('department', ''),
                        job=crew_data.get('job', ''),
                    )

        return movie, created

    def _get_or_create_person(self, person_data):
        """Kişi oluştur veya al."""
        person, _ = Person.objects.get_or_create(
            tmdb_id=person_data['id'],
            defaults={
                'name': person_data.get('name', ''),
                'profile_path': person_data.get('profile_path'),
            }
        )
        return person
