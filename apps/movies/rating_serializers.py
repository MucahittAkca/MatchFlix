from rest_framework import serializers
from apps.movies.models import Rating, Movie
from django.contrib.auth import get_user_model

User = get_user_model()


class RatingSerializer(serializers.ModelSerializer):
    """Puanlama serializer'ı"""
    user = serializers.StringRelatedField(read_only=True)
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    movie_poster_url = serializers.CharField(source='movie.poster_url', read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'user', 'movie', 'movie_title', 'movie_poster_url', 'score', 'review', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class RatingCreateUpdateSerializer(serializers.ModelSerializer):
    """Puanlama oluşturma ve güncelleme serializer'ı"""
    class Meta:
        model = Rating
        fields = ['movie', 'score', 'review']

    def validate_score(self, value):
        """Puan doğrulama"""
        if not (1 <= value <= 10):
            raise serializers.ValidationError('Puan 1-10 arasında olmalıdır.')
        return value


class RatingDetailSerializer(serializers.ModelSerializer):
    """Detaylı puanlama serializer'ı (film bilgileri ile)"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    movie_data = serializers.SerializerMethodField()

    class Meta:
        model = Rating
        fields = ['id', 'user_username', 'movie_data', 'score', 'review', 'created_at']

    def get_movie_data(self, obj):
        """Film bilgilerini döndür"""
        return {
            'id': obj.movie.id,
            'title': obj.movie.title,
            'poster_url': obj.movie.poster_url,
            'vote_average': obj.movie.vote_average,
            'year': obj.movie.year,
        }


class UserRatingsSerializer(serializers.Serializer):
    """Kullanıcının puanladığı filmler"""
    id = serializers.IntegerField()
    username = serializers.CharField()
    total_ratings = serializers.IntegerField()
    avg_rating = serializers.FloatField()
    ratings = RatingDetailSerializer(many=True, read_only=True)
