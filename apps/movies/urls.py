from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GenreViewSet, PersonViewSet, MovieViewSet, RatingViewSet

app_name = 'movies'

router = DefaultRouter()
router.register('genres', GenreViewSet, basename='genre')
router.register('persons', PersonViewSet, basename='person')
router.register('movies', MovieViewSet, basename='movie')
router.register('ratings', RatingViewSet, basename='rating')

urlpatterns = [
    path('', include(router.urls)),
]