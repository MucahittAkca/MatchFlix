from django.contrib import admin
from .models import UserTasteProfile, MovieLensMapping, RecommendationLog


@admin.register(UserTasteProfile)
class UserTasteProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_rated_movies', 'average_rating', 'rating_style', 'updated_at']
    list_filter = ['rating_style']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Kullanıcı', {
            'fields': ('user',)
        }),
        ('Tür Tercihleri', {
            'fields': ('genre_weights', 'preferred_decades'),
            'classes': ('collapse',),
        }),
        ('Favori Kişiler', {
            'fields': ('favorite_actors', 'favorite_directors'),
            'classes': ('collapse',),
        }),
        ('İstatistikler', {
            'fields': ('total_rated_movies', 'average_rating', 'rating_style'),
        }),
        ('Tarihler', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(MovieLensMapping)
class MovieLensMappingAdmin(admin.ModelAdmin):
    list_display = ['movielens_id', 'tmdb_id', 'movie', 'imdb_id']
    search_fields = ['movielens_id', 'tmdb_id', 'movie__title']
    raw_id_fields = ['movie']


@admin.register(RecommendationLog)
class RecommendationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'recommendation_type', 'final_score', 'was_clicked', 'was_rated', 'created_at']
    list_filter = ['recommendation_type', 'was_clicked', 'was_rated', 'created_at']
    search_fields = ['user__username', 'movie__title']
    date_hierarchy = 'created_at'
    raw_id_fields = ['user', 'movie']
