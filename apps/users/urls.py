from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserViewSet, FriendshipViewSet

app_name = 'users'

# User endpoints
register_view = UserViewSet.as_view({'post': 'register'})
login_view = UserViewSet.as_view({'post': 'login'})
logout_view = UserViewSet.as_view({'post': 'logout'})
profile_view = UserViewSet.as_view({'get': 'profile'})
update_profile_view = UserViewSet.as_view({'put': 'update_profile', 'patch': 'update_profile'})
user_detail_view = UserViewSet.as_view({'get': 'user_detail'})

# Friendship endpoints
friends_list_view = FriendshipViewSet.as_view({'get': 'list_friends'})
friends_pending_view = FriendshipViewSet.as_view({'get': 'pending'})
friends_sent_view = FriendshipViewSet.as_view({'get': 'sent'})
friends_send_request_view = FriendshipViewSet.as_view({'post': 'send_request'})
friends_accept_view = FriendshipViewSet.as_view({'post': 'accept'})
friends_reject_view = FriendshipViewSet.as_view({'post': 'reject'})
friends_remove_view = FriendshipViewSet.as_view({'post': 'remove'})
friends_block_view = FriendshipViewSet.as_view({'post': 'block'})
friends_search_view = FriendshipViewSet.as_view({'get': 'search'})

urlpatterns = [
    # Auth
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile
    path('profile/', profile_view, name='profile'),
    path('update_profile/', update_profile_view, name='update_profile'),
    path('user_detail/', user_detail_view, name='user_detail'),
    
    # Friendship
    path('friends/', friends_list_view, name='friends_list'),
    path('friends/pending/', friends_pending_view, name='friends_pending'),
    path('friends/sent/', friends_sent_view, name='friends_sent'),
    path('friends/send_request/', friends_send_request_view, name='friends_send_request'),
    path('friends/accept/', friends_accept_view, name='friends_accept'),
    path('friends/reject/', friends_reject_view, name='friends_reject'),
    path('friends/remove/', friends_remove_view, name='friends_remove'),
    path('friends/block/', friends_block_view, name='friends_block'),
    path('friends/search/', friends_search_view, name='friends_search'),
]
