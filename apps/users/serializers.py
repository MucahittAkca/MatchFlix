from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    """Kullanıcı kayıt serializer'ı"""
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']

    def validate(self, data):
        """Şifreleri kontrol et"""
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Şifreler eşleşmiyor.'})
        return data

    def create(self, validated_data):
        """Kullanıcı oluştur"""
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Kullanıcı giriş serializer'ı"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Kullanıcıyı doğrula"""
        from django.contrib.auth import authenticate
        
        user = authenticate(
            username=data['username'],
            password=data['password']
        )
        
        if not user:
            raise serializers.ValidationError('Kullanıcı adı veya şifre yanlış.')
        
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    """Kullanıcı profil serializer'ı"""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'bio', 'profile_picture', 'date_of_birth',
            'total_movies_watched', 'avg_rating',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'total_movies_watched', 'avg_rating']


class UserUpdateSerializer(serializers.ModelSerializer):
    """Kullanıcı profil güncelleme serializer'ı"""
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email',
            'bio', 'profile_picture', 'date_of_birth'
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    """Detaylı kullanıcı serializer'ı (istatistikler ile)"""
    total_ratings = serializers.SerializerMethodField()
    watched_movies_count = serializers.SerializerMethodField()
    avg_movie_rating = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'bio', 'profile_picture', 'date_of_birth',
            'total_ratings', 'watched_movies_count', 'avg_movie_rating',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_ratings(self, obj):
        """Toplam puanlama sayısı"""
        return obj.ratings.count()

    def get_watched_movies_count(self, obj):
        """İzlenen film sayısı (puanlanmış filmler)"""
        return obj.ratings.values('movie').distinct().count()

    def get_avg_movie_rating(self, obj):
        """Ortalama puan"""
        from django.db.models import Avg
        avg = obj.ratings.aggregate(Avg('score'))['score__avg']
        return round(avg, 1) if avg else 0


class TokenResponseSerializer(serializers.Serializer):
    """Token yanıt serializer'ı"""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


# Friendship Serializers
from .models import Friendship, CompatibilityScore


class FriendshipSerializer(serializers.ModelSerializer):
    """Arkadaşlık serializer'ı"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    friend_username = serializers.CharField(source='friend.username', read_only=True)
    user_profile_picture = serializers.ImageField(source='user.profile_picture', read_only=True)
    friend_profile_picture = serializers.ImageField(source='friend.profile_picture', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Friendship
        fields = [
            'id', 'user', 'friend', 'user_username', 'friend_username',
            'user_profile_picture', 'friend_profile_picture',
            'status', 'status_display', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'created_at', 'updated_at']


class FriendshipCreateSerializer(serializers.Serializer):
    """Arkadaşlık isteği gönderme serializer'ı"""
    friend_username = serializers.CharField(max_length=150)

    def validate_friend_username(self, value):
        try:
            friend = User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('Kullanıcı bulunamadı.')
        
        request = self.context.get('request')
        if request and friend == request.user:
            raise serializers.ValidationError('Kendinize arkadaşlık isteği gönderemezsiniz.')
        
        # Zaten arkadaş mı kontrol et
        existing = Friendship.objects.filter(
            user=request.user, friend=friend
        ).first() or Friendship.objects.filter(
            user=friend, friend=request.user
        ).first()
        
        if existing:
            if existing.status == 'accepted':
                raise serializers.ValidationError('Bu kullanıcı zaten arkadaşınız.')
            elif existing.status == 'pending':
                raise serializers.ValidationError('Zaten bekleyen bir istek var.')
            elif existing.status == 'blocked':
                raise serializers.ValidationError('Bu kullanıcı engellenmiş.')
        
        return value


class FriendSerializer(serializers.ModelSerializer):
    """Arkadaş listesi için basit serializer"""
    total_ratings = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture', 'total_ratings']

    def get_total_ratings(self, obj):
        return obj.ratings.count()


class CompatibilityScoreSerializer(serializers.ModelSerializer):
    """Uyumluluk skoru serializer'ı"""
    user_1_username = serializers.CharField(source='user_1.username', read_only=True)
    user_2_username = serializers.CharField(source='user_2.username', read_only=True)

    class Meta:
        model = CompatibilityScore
        fields = [
            'id', 'user_1', 'user_2', 'user_1_username', 'user_2_username',
            'score', 'common_movies', 'similar_genres', 'similar_actors',
            'similar_directors', 'calculated_at'
        ]
        read_only_fields = ['id', 'calculated_at']