from shutil import move
from unittest.mock import Base
from venv import create
from datetime import datetime
from django.core.management.base import BaseCommand
from apps.movies.models import Movie, Genre, Person, MovieCast, MovieCrew
from apps.movies.services import tmdb_service


class Command(BaseCommand):
    help = 'TMDB\' den popüler filmleri çeker.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pages',
            type=int,
            default=3,
            help='Kaç sayfa film çekilecek (her sayfa 20 film)'
        )


    def handle(self, *args, **options):
        pages = options['pages']
        total_created = 0 

        self.stdout.write(f'Popüler filmler çekiliyor ({pages} sayfa)...\n')

        for page in range(1, pages + 1):
            self.stdout.write(f'Sayfa {page}/{pages}...')

            data = tmdb_service.get_popular_movies(page=page)
            movies_data = data.get('results', [])

            for movie_data in movies_data:
                #Film detaylarını al (cast ve ekip için)
                details = tmdb_service.get_movie_details(movie_data['id'])

                #filmi kaydet
                movie, created = self._save_movie(details)

                if created:
                    total_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ {movie.title} ({movie.year})')
                    )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Toplam {total_created} film eklendi!')
        )

    def _save_movie(self, data):
        """Film verisini kaydet."""
        # release_date'i parse et
        release_date = None
        if data.get('release_date'):
            try:
                release_date = datetime.strptime(data.get('release_date'), '%Y-%m-%d').date()
            except (ValueError, TypeError):
                release_date = None
        
        #Film oluştur/güncelle
        movie, created = Movie.objects.update_or_create(
            tmdb_id = data['id'],
            defaults={
                'imdb_id':data.get('imdb_id'),
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

        if 'genres' in data:
            genre_ids = [g['id'] for g in data['genres']]
            genres = Genre.objects.filter(tmdb_id__in=genre_ids)
            movie.genres.set(genres)


        if 'credits' in data and 'cast' in data['credits']:
            for cast_data in data['credits']['cast'][:10]:
                person = self._get_or_create_person(cast_data)
                MovieCast.objects.get_or_create(
                    movie=movie,
                    person=person,
                    character_name = cast_data.get('character', ''),
                    defaults={'cast_order': cast_data.get('order', 0)},
                )

        #crew ekle(sadece yönetmen)
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
        person, _ =Person.objects.get_or_create(
            tmdb_id = data['id'],
            defaults={
                'name': data.get('name', ''),
                'profile_path': data.get('profile_path'),
                'known_for_department': data.get('known_for_department', ''),
                'gender': data.get('gender', 0),
                "popularity": data.get('popularity', 0),
            }
        )
        return person