from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Friendship, CompatibilityScore


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'total_movies_watched', 'avg_rating']
    list_filter = ['is_staff', 'is_superuser', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Ek Bilgiler', {
            'fields': ('bio', 'profile_picture', 'date_of_birth', 'total_movies_watched', 'avg_rating')
        }),
    )


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ['user', 'friend', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'friend__username']
    raw_id_fields = ['user', 'friend']


@admin.register(CompatibilityScore)
class CompatibilityScoreAdmin(admin.ModelAdmin):
    list_display = ['user_1', 'user_2', 'score', 'common_movies', 'calculated_at']
    list_filter = ['calculated_at']
    search_fields = ['user_1__username', 'user_2__username']
    raw_id_fields = ['user_1', 'user_2']