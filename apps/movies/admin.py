from django.contrib import admin
from .models import Genre, Person, Movie, MovieCast, MovieCrew, Rating, Watchlist, WatchedMovie

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_tr', 'tmdb_id']
    search_fields = ['name','name_tr']


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['name', 'known_for_department', 'birthday', 'popularity']
    list_filter = ['known_for_department', 'gender']
    search_fields = ['name']
    readonly_fields = ['profile_url']


class MovieCastInline(admin.TabularInline):
    model = MovieCast
    extra = 0
    autocomplete_fields = ['person']


class MovieCrewInline(admin.TabularInline):
    model = MovieCrew
    extra = 0
    autocomplete_fields = ['person']


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'release_date', 'vote_average', 'popularity', 'status']
    list_filter = ['status', 'release_date', 'adult', 'original_language']
    search_fields = ['title', 'original_title', 'tmdb_id']
    filter_horizontal = ['genres']
    readonly_fields = ['poster_url', 'backdrop_url', 'created_at', 'updated_at']
    inlines = [MovieCastInline, MovieCrewInline]

    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('tmdb_id', 'imdb_id', 'title', 'original_title', 'tagline', 'overview')
        }),
        ('Görsel', {
            'fields': ('poster_path', 'poster_url', 'backdrop_path', 'backdrop_url')
        }),
        ('Detaylar', {
            'fields': ('release_date', 'runtime', 'genres', 'original_language', 'status', 'adult')
        }),
        ('Puanlama', {
            'fields': ('vote_average', 'vote_count', 'popularity')
        }),
        ('Finansal', {
            'fields': ('budget', 'revenue'),
            'classes': ('collapse')
        }),
        ('Metadata', {
            'fields': ('homepage', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MovieCast)
class MovieCastAdmin(admin.ModelAdmin):
    list_display = ['person', 'movie', 'character_name', 'cast_order']
    list_filter = ['movie']
    search_fields = ['person__name', 'movie__title', 'character_name']
    autocomplete_fields = ['movie', 'person']


@admin.register(MovieCrew)
class MovieCrewAdmin(admin.ModelAdmin):
    list_display = ['person', 'movie', 'job', 'department']
    list_filter = ['job', 'department']
    search_fields = ['person__name', 'movie__title']
    autocomplete_fields = ['movie', 'person']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'score', 'created_at']
    list_filter = ['score', 'created_at']
    search_fields = ['user__username', 'movie__title']
    autocomplete_fields = ['movie']


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'movie__title']
    autocomplete_fields = ['movie']


@admin.register(WatchedMovie)
class WatchedMovieAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'liked', 'watched_at']
    list_filter = ['liked', 'watched_at']
    search_fields = ['user__username', 'movie__title']
    autocomplete_fields = ['movie']