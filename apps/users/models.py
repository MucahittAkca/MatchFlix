from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):   
    # E-posta benzersiz olmalı
    email = models.EmailField(unique=True, verbose_name='E-posta')
    
    bio = models.TextField(max_length=500, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True
    )
    date_of_birth = models.DateField(blank=True, null=True)

    # Onboarding durumu
    onboarding_completed = models.BooleanField(
        default=False, 
        verbose_name='Onboarding Tamamlandı'
    )
    favorite_genres = models.ManyToManyField(
        'movies.Genre',
        blank=True,
        related_name='fans',
        verbose_name='Favori Türler'
    )

    #istatistik cache icin daha sonra
    total_movies_watched = models.IntegerField(default=0)
    avg_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.0
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'Kullanıcı'
        verbose_name_plural = 'Kullanıcılar'

    def __str__(self):
        return self.username
    
    def get_friends(self):
        """Kabul edilen arkadaşları döndür"""
        from django.db.models import Q
        friendships = Friendship.objects.filter(
            Q(user=self, status='accepted') | Q(friend=self, status='accepted')
        )
        friends = []
        for friendship in friendships:
            if friendship.user == self:
                friends.append(friendship.friend)
            else:
                friends.append(friendship.user)
        return friends
    
    def get_pending_requests(self):
        """Bekleyen arkadaşlık isteklerini döndür (bana gelenler)"""
        return Friendship.objects.filter(friend=self, status='pending')
    
    def get_sent_requests(self):
        """Gönderilen arkadaşlık isteklerini döndür"""
        return Friendship.objects.filter(user=self, status='pending')


class Friendship(models.Model):
    """Arkadaşlık ilişkileri"""
    STATUS_CHOICES = [
        ('pending', 'Beklemede'),
        ('accepted', 'Kabul Edildi'),
        ('rejected', 'Reddedildi'),
        ('blocked', 'Engellendi'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='friendships_sent',
        verbose_name='Gönderen'
    )
    friend = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='friendships_received',
        verbose_name='Alıcı'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='Durum'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'friendships'
        verbose_name = 'Arkadaşlık'
        verbose_name_plural = 'Arkadaşlıklar'
        unique_together = ['user', 'friend']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} → {self.friend.username} ({self.get_status_display()})"
    
    def accept(self):
        """Arkadaşlık isteğini kabul et"""
        self.status = 'accepted'
        self.save()
    
    def reject(self):
        """Arkadaşlık isteğini reddet"""
        self.status = 'rejected'
        self.save()
    
    def block(self):
        """Kullanıcıyı engelle"""
        self.status = 'blocked'
        self.save()


class CompatibilityScore(models.Model):
    """İki kullanıcı arasındaki film uyumluluk skoru"""
    user_1 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='compatibility_as_user1'
    )
    user_2 = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='compatibility_as_user2'
    )
    score = models.IntegerField(
        default=0,
        help_text="0-100 arası uyumluluk puanı"
    )
    common_movies = models.IntegerField(default=0)
    similar_genres = models.JSONField(default=dict, blank=True)
    similar_actors = models.JSONField(default=dict, blank=True)
    similar_directors = models.JSONField(default=dict, blank=True)
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compatibility_scores'
        verbose_name = 'Uyumluluk Skoru'
        verbose_name_plural = 'Uyumluluk Skorları'
        unique_together = ['user_1', 'user_2']

    def __str__(self):
        return f"{self.user_1.username} ↔ {self.user_2.username}: %{self.score}"