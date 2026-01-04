from ssl import create_default_context
from venv import create
from django.core.management.base import BaseCommand
from apps.movies.models import Genre
from apps.movies.services import tmdb_service


class Command(BaseCommand):
    help = 'TMDB\'den film türlerini çeker ve veritabanına kaydeder.'

    def handle(self, *args, **options):
        self.stdout.write('TMDB türleri çekiliyor...')

        genres_data = tmdb_service.get_genres()

        created_count = 0
        updated_count = 0

        for genre_data in genres_data:
            genre, created = Genre.objects.update_or_create(
                tmdb_id = genre_data['id'],
                defaults={
                    'name': genre_data['name'],
                    'name_tr': genre_data['name']
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Oluşturuldu: {genre.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(f' Güncellendi: {genre.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Tamamlandı! {created_count} yeni, {updated_count} güncellendi.'
            )
        )