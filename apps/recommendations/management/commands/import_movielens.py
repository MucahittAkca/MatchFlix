"""
MovieLens Veri Seti Import
===========================
MovieLens filmlerini TMDB ID'leri ile eslestir
"""

import os
import pandas as pd
from django.core.management.base import BaseCommand
from apps.movies.models import Movie
from apps.recommendations.models import MovieLensMapping


class Command(BaseCommand):
    help = 'Import MovieLens links.csv for TMDB ID mapping'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            required=True,
            help='Path to MovieLens folder (e.g., ./ml-latest-small)'
        )
    
    def handle(self, *args, **options):
        path = options['path']
        links_file = os.path.join(path, 'links.csv')
        
        if not os.path.exists(links_file):
            self.stderr.write(f"Dosya bulunamadi: {links_file}")
            return
        
        self.stdout.write("[INFO] MovieLens links.csv okunuyor...")
        
        # links.csv oku
        links_df = pd.read_csv(links_file)
        self.stdout.write(f"   Toplam film: {len(links_df)}")
        
        # Bizim DB'deki TMDB ID'leri
        our_tmdb_ids = set(Movie.objects.values_list('tmdb_id', flat=True))
        self.stdout.write(f"   Bizim DB'deki film: {len(our_tmdb_ids)}")
        
        created = 0
        matched = 0
        
        for _, row in links_df.iterrows():
            tmdb_id = row.get('tmdbId')
            if pd.isna(tmdb_id):
                continue
            
            tmdb_id = int(tmdb_id)
            movielens_id = int(row['movieId'])
            
            # Esleyen film var mi?
            movie = None
            if tmdb_id in our_tmdb_ids:
                movie = Movie.objects.filter(tmdb_id=tmdb_id).first()
                if movie:
                    matched += 1
            
            # Mapping olustur
            imdb_id = row.get('imdbId')
            imdb_str = f"tt{int(imdb_id):07d}" if pd.notna(imdb_id) else None
            
            MovieLensMapping.objects.update_or_create(
                movielens_id=movielens_id,
                defaults={
                    'tmdb_id': tmdb_id,
                    'movie': movie,
                    'imdb_id': imdb_str
                }
            )
            created += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"\n[DONE] Tamamlandi!"
            f"\n   Toplam mapping: {created}"
            f"\n   Eslesen film: {matched}"
            f"\n   Eslesme orani: %{(matched/created*100):.1f}" if created > 0 else ""
        ))

