"""
Recommendation Signals
======================
Otomatik profil oluşturma ve güncelleme
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from apps.movies.models import Rating
from apps.recommendations.models import UserTasteProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_taste_profile(sender, instance, created, **kwargs):
    """Yeni kullanıcı için taste profile oluştur"""
    if created:
        UserTasteProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=Rating)
def update_taste_profile_on_rating(sender, instance, **kwargs):
    """Rating eklendiğinde/güncellendiğinde profili güncelle"""
    try:
        profile, created = UserTasteProfile.objects.get_or_create(user=instance.user)
        # Profili güncelle (async olabilir, şimdilik sync)
        profile.update_from_ratings()
    except Exception as e:
        print(f"Profil güncelleme hatası: {e}")

