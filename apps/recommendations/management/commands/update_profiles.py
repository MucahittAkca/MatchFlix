"""
Update User Taste Profiles
===========================
Tüm kullanıcıların zevk profillerini güncelle
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.recommendations.models import UserTasteProfile
from apps.movies.models import Rating

User = get_user_model()


class Command(BaseCommand):
    help = 'Update all user taste profiles based on their ratings'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Update only specific user (username)'
        )
        parser.add_argument(
            '--create-missing',
            action='store_true',
            help='Create profiles for users who dont have one'
        )
    
    def handle(self, *args, **options):
        if options['user']:
            # Tek kullanıcı
            try:
                user = User.objects.get(username=options['user'])
                users = [user]
            except User.DoesNotExist:
                self.stderr.write(f"Kullanıcı bulunamadı: {options['user']}")
                return
        else:
            # Tüm kullanıcılar
            users = User.objects.all()
        
        self.stdout.write(f"[INFO] {len(users)} kullanici islenecek...")
        
        created = 0
        updated = 0
        skipped = 0
        
        for user in users:
            # Profil var mı?
            profile, is_new = UserTasteProfile.objects.get_or_create(user=user)
            
            if is_new:
                created += 1
            
            # Rating var mı?
            if Rating.objects.filter(user=user).exists():
                profile.update_from_ratings()
                updated += 1
                self.stdout.write(f"  [OK] {user.username}: {profile.total_rated_movies} film, avg={profile.average_rating}")
            else:
                skipped += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"\n[DONE] Tamamlandi!"
            f"\n   Olusturulan: {created}"
            f"\n   Guncellenen: {updated}"
            f"\n   Atlanan (rating yok): {skipped}"
        ))

