"""
Mevcut filmlerin Türkçe çevirisini kontrol et ve düzelt
Non-Latin başlıkları ve boş overview'ları İngilizce fallback ile güncelle
"""
from django.core.management.base import BaseCommand
from apps.movies.models import Movie
from apps.movies.services import tmdb_service


class Command(BaseCommand):
    help = 'Non-Latin başlıklı ve boş açıklamalı filmleri düzelt'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='İşlenecek maksimum film sayısı (varsayılan: 100)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Değişiklikleri kaydetmeden sadece listele'
        )

    def is_non_latin(self, text):
        """Metnin Latin olmayan karakterler içerip içermediğini kontrol et"""
        if not text:
            return False
        latin_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-:;\'"()[]{}@#$%&*+=/<>~`')
        non_latin_count = sum(1 for char in text if char not in latin_chars)
        return non_latin_count > len(text) * 0.3

    def handle(self, *args, **options):
        limit = options['limit']
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.WARNING(f'Film çevirilerini kontrol ediyorum (limit: {limit})...'))
        
        # Sorunlu filmleri bul
        movies = Movie.objects.all()[:limit]
        
        problematic_movies = []
        for movie in movies:
            needs_fix = False
            reason = []
            
            if self.is_non_latin(movie.title):
                needs_fix = True
                reason.append('non-latin title')
            
            if not movie.overview:
                needs_fix = True
                reason.append('empty overview')
            
            if needs_fix:
                problematic_movies.append((movie, reason))
        
        self.stdout.write(f'Sorunlu film sayısı: {len(problematic_movies)}')
        
        if not problematic_movies:
            self.stdout.write(self.style.SUCCESS('Tüm filmler düzgün görünüyor!'))
            return
        
        fixed_count = 0
        failed_count = 0
        
        for movie, reasons in problematic_movies:
            # Non-Latin karakterler için güvenli yazım
            safe_title = movie.title.encode('ascii', 'replace').decode('ascii') if movie.title else '(no title)'
            self.stdout.write(f'\n[Film] {safe_title} (ID: {movie.tmdb_id})')
            self.stdout.write(f'   Sorun: {", ".join(reasons)}')
            
            if dry_run:
                continue
            
            try:
                # TMDB'den güncel veri al
                full_data = tmdb_service.get_movie_with_fallback(movie.tmdb_id)
                
                if not full_data:
                    self.stdout.write(self.style.ERROR(f'   [X] TMDB verisi alinamadi'))
                    failed_count += 1
                    continue
                
                # Güncelle
                old_title = movie.title
                old_overview = movie.overview[:50] if movie.overview else '(bos)'
                
                if 'non-latin title' in reasons and full_data.get('title'):
                    movie.title = full_data.get('title')
                
                if 'empty overview' in reasons and full_data.get('overview'):
                    movie.overview = full_data.get('overview')
                
                # Tagline ve runtime da kontrol et
                if not movie.tagline and full_data.get('tagline'):
                    movie.tagline = full_data.get('tagline')
                if not movie.runtime and full_data.get('runtime'):
                    movie.runtime = full_data.get('runtime')
                
                movie.save()
                
                self.stdout.write(self.style.SUCCESS(f'   [OK] Guncellendi'))
                safe_old = old_title.encode('ascii', 'replace').decode('ascii') if old_title else '?'
                safe_new = movie.title.encode('ascii', 'replace').decode('ascii') if movie.title else '?'
                self.stdout.write(f'      Baslik: {safe_old} -> {safe_new}')
                if movie.overview:
                    safe_overview = movie.overview[:50].encode('ascii', 'replace').decode('ascii')
                    self.stdout.write(f'      Overview: (eklendi) {safe_overview}...')
                
                fixed_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   [X] Hata: {e}'))
                failed_count += 1
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'[OK] Duzeltilen: {fixed_count}'))
        if failed_count:
            self.stdout.write(self.style.ERROR(f'[X] Basarisiz: {failed_count}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[!] DRY-RUN modu - degisiklikler kaydedilmedi.'))
            self.stdout.write('Gercek duzeltme icin: python manage.py fix_movie_translations')

