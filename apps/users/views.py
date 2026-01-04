from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.db.models import Q

from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserSerializer,
    UserUpdateSerializer,
    UserDetailSerializer,
    TokenResponseSerializer,
    FriendshipSerializer,
    FriendshipCreateSerializer,
    FriendSerializer,
    CompatibilityScoreSerializer
)
from .models import Friendship, CompatibilityScore

User = get_user_model()


class UserViewSet(viewsets.ViewSet):
    """
    Kullanıcı API Endpoints
    - register: Kullanıcı kaydı
    - login: Kullanıcı girişi (JWT token)
    - profile: Kendi profili (authenticated)
    - update_profile: Profil güncelleme
    - user_detail: Başka bir kullanıcının profili
    """

    def get_permissions(self):
        """İzin ayarla"""
        if self.action in ['register', 'login']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Yeni kullanıcı kaydı
        POST /api/users/register/
        """
        serializer = UserRegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Token oluştur
            refresh = RefreshToken.for_user(user)
            
            response_data = {
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'message': 'Kayıt başarılı!'
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Kullanıcı girişi
        POST /api/users/login/
        """
        serializer = UserLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Token oluştur
            refresh = RefreshToken.for_user(user)
            
            response_data = {
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'message': 'Giriş başarılı!'
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """
        Kendi profili (authenticated)
        GET /api/users/profile/
        """
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """
        Profil güncelle
        PUT /api/users/update_profile/
        """
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'user': UserDetailSerializer(request.user).data,
                    'message': 'Profil güncellendi!'
                },
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def user_detail(self, request):
        """
        Başka bir kullanıcının profili
        GET /api/users/user_detail/?username=username
        """
        username = request.query_params.get('username')
        
        if not username:
            return Response(
                {'error': 'username parametresi gerekli'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(username=username)
            serializer = UserDetailSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'Kullanıcı bulunamadı'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Çıkış (token'ı blacklist'e ekle)
        POST /api/users/logout/
        """
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'message': 'Çıkış başarılı!'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class FriendshipViewSet(viewsets.ViewSet):
    """
    Arkadaşlık API Endpoints
    - list: Arkadaş listesi
    - pending: Bekleyen istekler
    - sent: Gönderilen istekler
    - send_request: Arkadaşlık isteği gönder
    - accept: İsteği kabul et
    - reject: İsteği reddet
    - remove: Arkadaşı sil
    - block: Kullanıcıyı engelle
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def list_friends(self, request):
        """
        Arkadaş listesi
        GET /api/users/friends/list_friends/
        """
        friends = request.user.get_friends()
        serializer = FriendSerializer(friends, many=True)
        return Response({
            'count': len(friends),
            'friends': serializer.data
        })

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Bekleyen arkadaşlık istekleri (bana gelenler)
        GET /api/users/friends/pending/
        """
        pending_requests = request.user.get_pending_requests()
        serializer = FriendshipSerializer(pending_requests, many=True)
        return Response({
            'count': pending_requests.count(),
            'requests': serializer.data
        })

    @action(detail=False, methods=['get'])
    def sent(self, request):
        """
        Gönderilen arkadaşlık istekleri
        GET /api/users/friends/sent/
        """
        sent_requests = request.user.get_sent_requests()
        serializer = FriendshipSerializer(sent_requests, many=True)
        return Response({
            'count': sent_requests.count(),
            'requests': serializer.data
        })

    @action(detail=False, methods=['post'])
    def send_request(self, request):
        """
        Arkadaşlık isteği gönder
        POST /api/users/friends/send_request/
        Body: {"friend_username": "username"}
        """
        serializer = FriendshipCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            friend_username = serializer.validated_data['friend_username']
            friend = User.objects.get(username=friend_username)
            
            friendship = Friendship.objects.create(
                user=request.user,
                friend=friend,
                status='pending'
            )
            
            return Response({
                'message': f'{friend_username} kullanıcısına arkadaşlık isteği gönderildi.',
                'friendship': FriendshipSerializer(friendship).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def accept(self, request):
        """
        Arkadaşlık isteğini kabul et
        POST /api/users/friends/accept/
        Body: {"friendship_id": 1}
        """
        friendship_id = request.data.get('friendship_id')
        
        if not friendship_id:
            return Response({'error': 'friendship_id gerekli'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            friendship = Friendship.objects.get(id=friendship_id, friend=request.user, status='pending')
            friendship.accept()
            
            return Response({
                'message': f'{friendship.user.username} ile artık arkadaşsınız!',
                'friendship': FriendshipSerializer(friendship).data
            })
        except Friendship.DoesNotExist:
            return Response({'error': 'İstek bulunamadı'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def reject(self, request):
        """
        Arkadaşlık isteğini reddet
        POST /api/users/friends/reject/
        Body: {"friendship_id": 1}
        """
        friendship_id = request.data.get('friendship_id')
        
        if not friendship_id:
            return Response({'error': 'friendship_id gerekli'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            friendship = Friendship.objects.get(id=friendship_id, friend=request.user, status='pending')
            friendship.reject()
            
            return Response({'message': 'İstek reddedildi.'})
        except Friendship.DoesNotExist:
            return Response({'error': 'İstek bulunamadı'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def remove(self, request):
        """
        Arkadaşı sil
        POST /api/users/friends/remove/
        Body: {"friend_username": "username"}
        """
        friend_username = request.data.get('friend_username')
        
        if not friend_username:
            return Response({'error': 'friend_username gerekli'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            friend = User.objects.get(username=friend_username)
            friendship = Friendship.objects.filter(
                Q(user=request.user, friend=friend) | Q(user=friend, friend=request.user),
                status='accepted'
            ).first()
            
            if friendship:
                friendship.delete()
                return Response({'message': f'{friend_username} arkadaş listenizden çıkarıldı.'})
            else:
                return Response({'error': 'Arkadaşlık bulunamadı'}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({'error': 'Kullanıcı bulunamadı'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def block(self, request):
        """
        Kullanıcıyı engelle
        POST /api/users/friends/block/
        Body: {"username": "username"}
        """
        username = request.data.get('username')
        
        if not username:
            return Response({'error': 'username gerekli'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_to_block = User.objects.get(username=username)
            
            # Mevcut arkadaşlık var mı?
            friendship = Friendship.objects.filter(
                Q(user=request.user, friend=user_to_block) | Q(user=user_to_block, friend=request.user)
            ).first()
            
            if friendship:
                friendship.status = 'blocked'
                friendship.save()
            else:
                Friendship.objects.create(
                    user=request.user,
                    friend=user_to_block,
                    status='blocked'
                )
            
            return Response({'message': f'{username} engellendi.'})
        except User.DoesNotExist:
            return Response({'error': 'Kullanıcı bulunamadı'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Kullanıcı ara (arkadaş eklemek için)
        GET /api/users/friends/search/?q=username
        """
        query = request.query_params.get('q', '')
        
        if len(query) < 2:
            return Response({'error': 'En az 2 karakter girin'}, status=status.HTTP_400_BAD_REQUEST)
        
        users = User.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:20]
        
        serializer = FriendSerializer(users, many=True)
        return Response({
            'count': users.count(),
            'users': serializer.data
        })
