from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views import api_root
from .frontend_views import (
    landing, home, movie_detail, quick_match, explore, profile, friends, watchlist,
    register, login, logout, add_rating, edit_profile, toggle_watchlist,
    mark_as_watched, remove_from_watched, watched_movies, check_movie_status,
    send_friend_request, accept_friend_request, reject_friend_request, remove_friend,
    search_tmdb, import_movie_from_tmdb, tmdb_async_search, live_search, live_search_tmdb,
    forgot_password, reset_password, google_login, google_callback,
    onboarding, skip_onboarding, health_check
)


schema_view = get_schema_view(
    openapi.Info(
        title = "Matchflix API",
        default_version='v1',
        description="Film öneri ve sosyal platform API'si.",
        terms_of_service="https://www.matchflix.com/terms/",
        contact=openapi.Contact(email="contact@matchflix.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)



urlpatterns = [
    # Health check
    path('health/', health_check, name='health_check'),
    
    #auth
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', reset_password, name='reset_password'),
    path('auth/google/', google_login, name='google_login'),
    path('auth/google/callback/', google_callback, name='google_callback'),
    
    #pages
    path('', landing, name='landing'),
    path('home/', home, name='home'),
    path('onboarding/', onboarding, name='onboarding'),
    path('onboarding/skip/', skip_onboarding, name='skip_onboarding'),
    path('movie/<int:movie_id>/', movie_detail, name='movie_detail'),
    path('quick_match/', quick_match, name='quick_match'),
    path('explore/', explore, name='explore'),
    path('profile/', profile, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('friends/', friends, name='friends'),
    path('watchlist/', watchlist, name='watchlist'),
    path('watched/', watched_movies, name='watched_movies'),
    path('notifications/', include('apps.notifications.urls')),
    
    #api (frontend için)
    path('api/rating/add/', add_rating, name='add_rating'),
    path('api/watchlist/toggle/', toggle_watchlist, name='toggle_watchlist'),
    path('api/watched/mark/', mark_as_watched, name='mark_as_watched'),
    path('api/watched/remove/', remove_from_watched, name='remove_from_watched'),
    path('api/movie/<int:movie_id>/status/', check_movie_status, name='check_movie_status'),
    path('api/friends/send/', send_friend_request, name='send_friend_request'),
    path('api/friends/accept/', accept_friend_request, name='accept_friend_request'),
    path('api/friends/reject/', reject_friend_request, name='reject_friend_request'),
    path('api/friends/remove/', remove_friend, name='remove_friend'),
    path('api/tmdb/search/', search_tmdb, name='search_tmdb'),
    path('api/tmdb/import/', import_movie_from_tmdb, name='import_movie_from_tmdb'),
    path('api/tmdb/async-search/', tmdb_async_search, name='tmdb_async_search'),
    path('api/live-search/', live_search, name='live_search'),
    path('api/live-search/tmdb/', live_search_tmdb, name='live_search_tmdb'),
    
    #admin
    path('admin/', admin.site.urls),

    #api
    path('api/', include([
        path('movies/', include('apps.movies.urls')),
        path('users/', include('apps.users.urls')),
    ])),

    #api dokümantasyonu
    path('api/schema/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/schema/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/schema/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]

# Medya ve Static dosyalar (development için)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Static dosyalar için STATICFILES_DIRS kullanılır (collectstatic gerekmez)
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()