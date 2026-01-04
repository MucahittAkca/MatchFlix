from rest_framework import serializers
from .models import Genre, Person, Movie, MovieCast, MovieCrew

class GenreSerializer(serializers.ModelSerializer):
    """Tür serializeri"""

    class Meta:
        model = Genre
        fields = ['id', 'tmdb_id', 'name', 'name_tr']

    
class PersonListSerializer(serializers.ModelSerializer):
    """Kişi listesi için basit serializer"""
    profile_url = serializers.ReadOnlyField()

    class Meta:
        model = Person
        fields = ['id', 'tmdb_id', 'name', 'profile_url', 'known_for_department']

    
class PersonDetailSerializer(serializers.ModelSerializer):
    """Kişi detay serializeri"""
    profile_url = serializers.ReadOnlyField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = [
            'id', 'tmdb_id', 'name', 'profile_url', 'biography', 
            'birthday', 'deathday', 'age', 'place_of_birth',
            'known_for_department', 'gender', 'popularity',
        ]


    def get_age(self, obj):
        """Yaş hesapla"""
        if not obj.birthday:
            return None

        from datetime import date
        today = date.today()
        death_date = obj.deathday or today

        age = death_date.year - obj.birthday.year
        if death_date.month < obj.birthday.month or \
            ( death_date.month == obj.birthday.month and death_date.day < obj.birthday.day):
            age -=1

        return age
    

class MovieCastSerializer(serializers.ModelSerializer):
    """Film oyuncusu serializer'ı"""
    person = PersonListSerializer()

    class Meta:
        model = MovieCast
        fields = ['id', 'person', 'character_name', 'cast_order']


class MovieCrewSerializer(serializers.ModelSerializer):
    """Film ekibi serializeri"""
    person = PersonListSerializer()

    class Meta:
        model = MovieCrew
        fields = ['id', 'person', 'job', 'department']

class MovieListSerializer(serializers.ModelSerializer):
    """Film listesi için hafif serializer"""
    genres = GenreSerializer(many=True, read_only=True)
    poster_url = serializers.ReadOnlyField()
    year = serializers.ReadOnlyField()


    class Meta:
        model = Movie
        fields = [
            'id', 'tmdb_id', 'title', 'poster_url', 'year',
            'release_date', 'vote_average', 'vote_count',
            'popularity', 'genres', 'runtime'
        ]


class MovieDetailSerializer(serializers.ModelSerializer):
    """Film detay serializeri"""
    genres = GenreSerializer(many=True, read_only=True)
    cast = serializers.SerializerMethodField()
    director = serializers.SerializerMethodField()
    crew = serializers.SerializerMethodField()

    poster_url = serializers.ReadOnlyField()
    backdrop_url = serializers.ReadOnlyField()
    year = serializers.ReadOnlyField()

    class Meta:
        model = Movie
        fields = [
            'id', 'tmdb_id', 'imdb_id', 'title', 'original_title',
            'overview', 'tagline', 'poster_url', 'backdrop_url',
            'release_date', 'year', 'runtime', 'vote_average',
            'vote_count', 'popularity', 'status', 'adult',
            'budget', 'revenue', 'homepage', 'original_language',
            'genres', 'cast', 'director', 'crew', 'created_at'
        ]

    def get_cast(self, obj):
        """İlk 10 oyuncu"""
        cast = obj.cast.select_related('person').all()[:10]
        return MovieCastSerializer(cast, many=True).data

    def get_director(self, obj):
        """Yönetmen"""
        director_crew = obj.crew.filter(job='Director').select_related('person').first()
        if director_crew:
            return PersonListSerializer(director_crew.person).data
        return None
    
    def get_crew(self, obj):
        """Ekip (yönetmen hariç ilk 5)"""
        crew = obj.crew.exclude(job='Director').select_related('person')[:5]
        return MovieCrewSerializer(crew, many=True).data
    
class MovieSearchSerializer(serializers.Serializer):
    """Film Arama için serializeri"""
    query = serializers.CharField(required=True, max_length=255)
    page = serializers.IntegerField(default=1, min_value=1)