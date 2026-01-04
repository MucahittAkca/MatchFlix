from django_filters import FilterSet, NumberFilter
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend

from .models import Genre, Person, Movie, Rating
from .serializers import (
    GenreSerializer,
    PersonListSerializer,
    PersonDetailSerializer,
    MovieListSerializer,
    MovieDetailSerializer,
    MovieSearchSerializer
)
from .rating_serializers import (
    RatingSerializer,
    RatingCreateUpdateSerializer,
    RatingDetailSerializer,
)
from .services import tmdb_service


class MovieFilterSet(FilterSet):
    """Film filtreleme sınıfı"""
    rating_gte = NumberFilter(field_name='vote_average', lookup_expr='gte')
    rating_lte = NumberFilter(field_name='vote_average', lookup_expr='lte')
    year_gte = NumberFilter(field_name='release_date', lookup_expr='year__gte')
    year_lte = NumberFilter(field_name='release_date', lookup_expr='year__lte')
    genre = NumberFilter(field_name='genres__tmdb_id', lookup_expr='exact')
    
    class Meta:
        model = Movie
        fields = ['rating_gte', 'rating_lte', 'year_gte', 'year_lte', 'genre', 'original_language', 'adult']


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Tür endpoint'leri
    list: Tüm türler
    retrieve Tek tür detayı
    """

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [AllowAny] #herkes görüo


class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Kişi (oyuncu/yönetme) endpointleri
    list: Tüm Kişiler
    retrieve: Kişi detayı
    """

    queryset = Person.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['popularity', 'name']
    ordering = ['-popularity']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PersonDetailSerializer
        return PersonListSerializer
    

class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Film endpointleri

    list: Film listesi (filtreleme, arama, sıralama)
    retrieve: Film detayı
    search: Film arama
    popular: Popüler filmler
    trending: Trend filmler
    upcoming: Vizyona girecek filmler
    """

    queryset = Movie.objects.select_related().prefetch_related('genres', 'cast', 'crew')
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MovieFilterSet

    #arama
    search_fields = ['title', 'original_title', 'overview']

    #sıralama
    ordering_fields = ['release_date', 'vote_average', 'popularity', 'title']
    ordering = ['-popularity']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MovieDetailSerializer
        return MovieListSerializer
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Popüler Filmler"""
        movies = self.get_queryset().order_by('-popularity', '-vote_average')[:20]
        serializer = self.get_serializer(movies, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Trend filmler (bu hafta en çok izlenenler)"""
        movies = self.get_queryset().order_by('-popularity')
        serializer = self.get_serializer(movies, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Vizyona girecek filmler"""
        from datetime import date, timedelta

        today = date.today()
        next_month = today + timedelta(days=30)
        
        movies = self.get_queryset().filter(
            release_date__gte=today,
            release_date__lte=next_month
        ).order_by('release_date')
        
        serializer = self.get_serializer(movies, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def search(self, request):
        """
        TMDB'den film ara
        Body: {"query": "inception", "page": 1}
        """

        serializer = MovieSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data['query']
        page = serializer.validated_data.get('page', 1)


        #TMDB'den ara
        results = tmdb_service.search_movie(query, page)

        return Response({
            'query': query,
            'page': page,
            'total_pages': results.get('total_pages', 0),
            'total_results': results.get('total_results', 0),
            'results': results.get('results', [])
        })
    
    @action(detail=False, methods=['get'])
    def by_genre(self, request):
        """
        Türe göre filmler
        Query param: ?genre=28 (Aksiyon)
        """
        genre_id = request.query_params.get('genre')

        if not genre_id:
            return Response(
                {'error': 'genre parametresi gerekli'},
                status = status.HTTP_400_BAD_REQUEST
            )
        
        movies = self.get_queryset().filter(genres__id=genre_id)

        #Pagination
        page = self.paginate_queryset(movies)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(movies, many=True)
        return Response(serializer.data)
    
    
    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        """
        Benzer filmler
        Basit algoritma: Aynı türdeki, benzer puanlı filmler
        """

        movie = self.get_object()

        #Aynı türdeki filmler
        genre_ids = movie.genres.values_list('id', flat=True)

        similar_movies = Movie.objects.filter(
            genres__id__in=genre_ids
        ).exclude(
            id=movie.id
        ).distinct().order_by('-vote_average', '-popularity')[:10]


        serializer = self.get_serializer(similar_movies, many=True)
        return Response(serializer.data)


class RatingViewSet(viewsets.ModelViewSet):
    """
    Film puanlama endpointleri
    
    list: Tüm puanlamalar (filtreleme ile)
    create: Yeni puan ekle
    update: Puanı güncelle
    destroy: Puanı sil
    my_ratings: Kendi puanlarım
    movie_ratings: Bir filme verilen puanlamalar
    """
    
    queryset = Rating.objects.select_related('user', 'movie')
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['score', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RatingCreateUpdateSerializer
        return RatingDetailSerializer

    def perform_create(self, serializer):
        """Rating oluştur (user'ı otomatik set et)"""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Rating güncelle"""
        serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_ratings(self, request):
        """
        Kendi puanlarım
        GET /api/movies/ratings/my_ratings/
        """
        ratings = Rating.objects.filter(user=request.user).select_related('movie')
        page = self.paginate_queryset(ratings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def movie_ratings(self, request):
        """
        Bir filme verilen puanlamalar
        GET /api/movies/ratings/movie_ratings/?movie_id=1
        """
        movie_id = request.query_params.get('movie_id')
        
        if not movie_id:
            return Response(
                {'error': 'movie_id parametresi gerekli'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            movie = Movie.objects.get(id=movie_id)
            ratings = Rating.objects.filter(movie=movie).select_related('user')
            
            avg_score = ratings.aggregate(Avg('score'))['score__avg']
            
            page = self.paginate_queryset(ratings)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                response = self.get_paginated_response(serializer.data)
                response.data['avg_score'] = round(avg_score, 1) if avg_score else 0
                response.data['total_ratings'] = ratings.count()
                return response
            
            serializer = self.get_serializer(ratings, many=True)
            return Response({
                'results': serializer.data,
                'avg_score': round(avg_score, 1) if avg_score else 0,
                'total_ratings': ratings.count(),
            })
        except Movie.DoesNotExist:
            return Response(
                {'error': 'Film bulunamadı'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def user_ratings(self, request):
        """
        Bir kullanıcının puanlarını görüntüle
        GET /api/movies/ratings/user_ratings/?username=username
        """
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        username = request.query_params.get('username')
        
        if not username:
            return Response(
                {'error': 'username parametresi gerekli'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(username=username)
            ratings = Rating.objects.filter(user=user).select_related('movie')
            
            avg_score = ratings.aggregate(Avg('score'))['score__avg']
            
            page = self.paginate_queryset(ratings)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                response = self.get_paginated_response(serializer.data)
                response.data['user'] = {
                    'id': user.id,
                    'username': user.username,
                    'avg_score': round(avg_score, 1) if avg_score else 0,
                }
                return response
            
            serializer = self.get_serializer(ratings, many=True)
            return Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'avg_score': round(avg_score, 1) if avg_score else 0,
                },
                'results': serializer.data,
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'Kullanıcı bulunamadı'},
                status=status.HTTP_404_NOT_FOUND
            )