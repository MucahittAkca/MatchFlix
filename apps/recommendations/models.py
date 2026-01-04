"""
Recommendation Models
=====================
Öneri sistemi için veritabanı modelleri
"""

from django.db import models
from django.conf import settings


class UserTasteProfile(models.Model):
    """Kullanıcı film zevki profili"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='taste_profile'
    )
    
    # Tür tercihleri (genre_id: weight)
    genre_weights = models.JSONField(default=dict, blank=True)
    # Örnek: {"28": 0.8, "12": 0.6, "35": 0.3}
    
    # Favori kişiler
    favorite_actors = models.JSONField(default=list, blank=True)
    favorite_directors = models.JSONField(default=list, blank=True)
    
    # Tercih edilen dönemler
    preferred_decades = models.JSONField(default=dict, blank=True)
    # Örnek: {"2020s": 0.5, "2010s": 0.3}
    
    # Puan verme stili
    RATING_STYLE_CHOICES = [
        ('generous', 'Cömert'),      # Yüksek puanlar
        ('balanced', 'Dengeli'),     # Normal dağılım
        ('harsh', 'Eleştirel'),      # Düşük puanlar
    ]
    rating_style = models.CharField(
        max_length=20, 
        choices=RATING_STYLE_CHOICES,
        default='balanced'
    )
    
    # İstatistikler
    average_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    total_rated_movies = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Kullanıcı Zevk Profili'
        verbose_name_plural = 'Kullanıcı Zevk Profilleri'
    
    def __str__(self):
        return f"{self.user.username} - Zevk Profili"
    
    def update_from_ratings(self):
        """Kullanıcının puanlarından profili güncelle"""
        from apps.movies.models import Rating
        from collections import defaultdict
        
        ratings = Rating.objects.filter(user=self.user).select_related('movie').prefetch_related('movie__genres')
        
        if not ratings.exists():
            return
        
        # Tür ağırlıkları hesapla
        genre_scores = defaultdict(list)
        decade_scores = defaultdict(list)
        all_scores = []
        
        for rating in ratings:
            normalized_score = rating.score / 10.0
            all_scores.append(rating.score)
            
            # Türler
            for genre in rating.movie.genres.all():
                genre_scores[str(genre.id)].append(normalized_score)
            
            # Dönemler
            if rating.movie.release_date:
                year = rating.movie.release_date.year
                if year >= 2020:
                    decade = '2020s'
                elif year >= 2010:
                    decade = '2010s'
                elif year >= 2000:
                    decade = '2000s'
                else:
                    decade = 'classic'
                decade_scores[decade].append(normalized_score)
        
        # Ağırlıkları hesapla
        self.genre_weights = {
            genre_id: round(sum(scores) / len(scores), 2)
            for genre_id, scores in genre_scores.items()
        }
        
        self.preferred_decades = {
            decade: round(sum(scores) / len(scores), 2)
            for decade, scores in decade_scores.items()
        }
        
        # İstatistikler
        self.total_rated_movies = len(all_scores)
        self.average_rating = sum(all_scores) / len(all_scores)
        
        # Puan stili
        if self.average_rating >= 7.5:
            self.rating_style = 'generous'
        elif self.average_rating <= 5.5:
            self.rating_style = 'harsh'
        else:
            self.rating_style = 'balanced'
        
        self.save()


class MovieLensMapping(models.Model):
    """MovieLens ID - TMDB ID eşleştirmesi"""
    
    movielens_id = models.IntegerField(unique=True, db_index=True)
    movie = models.ForeignKey(
        'movies.Movie',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='movielens_mapping'
    )
    tmdb_id = models.IntegerField(db_index=True)
    imdb_id = models.CharField(max_length=20, null=True, blank=True)
    
    class Meta:
        verbose_name = 'MovieLens Eşleştirme'
        verbose_name_plural = 'MovieLens Eşleştirmeleri'
        indexes = [
            models.Index(fields=['movielens_id']),
            models.Index(fields=['tmdb_id']),
        ]
    
    def __str__(self):
        return f"ML:{self.movielens_id} → TMDB:{self.tmdb_id}"


class RecommendationLog(models.Model):
    """Öneri geçmişi (analiz ve A/B testing için)"""
    
    RECOMMENDATION_TYPES = [
        ('content', 'Content-Based'),
        ('collaborative', 'Collaborative'),
        ('hybrid', 'Hibrit'),
        ('quick_match', 'Hızlı Eşleşme'),
        ('similar', 'Benzer Filmler'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recommendation_logs'
    )
    movie = models.ForeignKey(
        'movies.Movie',
        on_delete=models.CASCADE,
        related_name='recommendation_logs'
    )
    
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    
    # Skorlar
    content_score = models.FloatField(null=True, blank=True)
    collab_score = models.FloatField(null=True, blank=True)
    final_score = models.FloatField()
    
    # Kullanıcı etkileşimi
    was_clicked = models.BooleanField(default=False)
    was_rated = models.BooleanField(default=False)
    rating_given = models.IntegerField(null=True, blank=True)
    
    # Context
    context = models.JSONField(default=dict, blank=True)
    # Örnek: {"mood": "happy", "time": "short", "era": "recent"}
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Öneri Logu'
        verbose_name_plural = 'Öneri Logları'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['recommendation_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} ← {self.movie.title} ({self.final_score:.2f})"
