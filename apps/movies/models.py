from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Genre(models.Model):
    """Film türleri (Aksiyon, Dram, vb.)"""
    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    name_tr = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'genres'
        verbose_name = 'Tür'
        verbose_name_plural = 'Türler'
        ordering = ['name']

    def __str__(self):
        return self.name_tr or self.name
    
class Person(models.Model):
    """Oyuncular, yönetmenler, yazarlar"""
    GENDER_CHOICES = [
        (0, 'Belirtilmemiş'),
        (1, 'Kadın'),
        (2, 'Erkek'),
        (3, 'Diğer'),
    ]

    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    profile_path = models.CharField(max_length=500, blank=True, null=True)
    biography = models.TextField(blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    deathday = models.DateField(blank=True, null=True)
    place_of_birth = models.CharField(max_length=255, blank=True, null=True)
    known_for_department = models.CharField(max_length=100, blank=True, null=True)
    gender = models.IntegerField(choices=GENDER_CHOICES, default=0)
    popularity = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'persons'
        verbose_name = 'Kişi'
        verbose_name_plural = 'Kişiler'
        ordering = ['-popularity']
        indexes = [
            models.Index(fields=['tmdb_id']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name
    
    @property
    def profile_url(self):
        """Profil fotoğrafı linki"""
        if self.profile_path:
            return f"https://image.tmdb.org/t/p/w185{self.profile_path}"
        return None

class Movie(models.Model):
    """Film Modeli - TMDB'den gelecek."""
    STATUS_CHOICES = [
        ('rumored', 'Söylenti'),
        ('planned', 'Planlanıyor'),
        ('in_production', 'Çekiliyor'),
        ('post_production', 'Post Prodüksiyon'),
        ('released', 'Vizyonda'),
        ('canceled', 'İptal'),
    ]

    # TMDB Bilgileri
    tmdb_id = models.IntegerField(unique=True, db_index=True)
    imdb_id = models.CharField(max_length=20, blank=True, null=True)

    #temel bilgiler
    title = models.CharField(max_length=255)
    original_title = models.CharField(max_length=255)
    overview = models.TextField(blank=True, null=True)
    tagline = models.CharField(max_length=500, blank=True, null=True)

    #Görsel
    poster_path = models.CharField(max_length=500, blank=True, null=True)
    backdrop_path = models.CharField(max_length=500, blank=True, null=True)


    #Tarih ve süre
    release_date = models.DateField(blank=True, null=True)
    runtime = models.IntegerField(blank=True, null=True, help_text="Dakika cinsinden")

    #Puanlama
    vote_average = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)]
    )
    vote_count = models.IntegerField(default=0)
    popularity = models.FloatField(default=0.0)

    # Dil ve Bölge
    original_language = models.CharField(max_length=10)

    #Durum
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='released')
    adult = models.BooleanField(default=False)


    #Bütçe
    budget = models.BigIntegerField(default=0)
    revenue = models.BigIntegerField(default=0)


    #İlişkiler
    genres = models.ManyToManyField(Genre, related_name='movies', blank=True)


    #Metadata
    homepage = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        db_table = 'movies'
        verbose_name = 'Film'
        verbose_name_plural = 'Filmler'
        ordering = ['-popularity', 'release_date']
        indexes = [
            models.Index(fields=['tmdb_id']),
            models.Index(fields=['title']),
            models.Index(fields=['release_date']),
            models.Index(fields=['-vote_average']),
        ]

    def __str__(self):
        year = self.release_date.year if self.release_date else 'N/A'
        return f"{self.title} ({year})"
    
    @property
    def poster_url(self):
        """Poster URL'i döndür"""
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/w500{self.poster_path}"
        # Placeholder resim - poster yoksa
        return "https://via.placeholder.com/500x750/1a1a2e/eee?text=No+Poster"
    
    @property
    def backdrop_url(self):
        """Backdrop linkini döndür"""
        if self.backdrop_path:
            return f"https://image.tmdb.org/t/p/original{self.backdrop_path}"
        # Backdrop yoksa poster kullan veya placeholder
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/original{self.poster_path}"
        return "https://via.placeholder.com/1920x1080/1a1a2e/eee?text=No+Image"
    
    @property
    def year(self):
        """Yıl döndür."""
        return self.release_date.year if self.release_date else None
    
class MovieCast(models.Model):
    """Film Oyuncuları"""
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='cast')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='movie_cast')
    character_name = models.CharField(max_length=255, blank=True, null=True)
    cast_order = models.IntegerField(default=0)


    class Meta:
        db_table = 'movie_cast'
        verbose_name = 'Film Oyuncusu'
        verbose_name_plural = 'Film Oyuncuları'
        unique_together = ['movie', 'person', 'character_name']
        ordering = ['cast_order']

    def __str__(self):
        return f"{self.person.name} as {self.character_name} in {self.movie.title}"
    

class MovieCrew(models.Model):
    """Film ekibi (yönetmen, yazar vs.)"""
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='crew')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='movie_crew')
    job = models.CharField(max_length=100) #Director, Writer, Producer
    department = models.CharField(max_length=100)

    class Meta:
        db_table = 'movie_crew'
        verbose_name = 'Film Ekibi'
        verbose_name_plural = 'Film Ekipleri'
        unique_together = ['movie', 'person', 'job']

    
    def __str__(self):
        return f"{self.person.name} - {self.job} ({self.movie.title})"


class Rating(models.Model):
    """Kullanıcı film puanlaması"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="1-10 arası puan"
    )
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ratings'
        verbose_name = 'Puanlama'
        verbose_name_plural = 'Puanlamalar'
        unique_together = ['user', 'movie']  # Bir kullanıcı bir filme sadece bir puan verebilir
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} rated {self.movie.title} {self.score}/10"


class Watchlist(models.Model):
    """Kullanıcı izleme listesi - İzleyeceklerim"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='in_watchlists')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'watchlist'
        verbose_name = 'İzleme Listesi'
        verbose_name_plural = 'İzleme Listeleri'
        unique_together = ['user', 'movie']
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"


class WatchedMovie(models.Model):
    """Kullanıcının izlediği filmler - İzlediklerim"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watched_movies')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='watched_by')
    liked = models.BooleanField(
        default=True,
        help_text="Beğendiyse True, beğenmediyse False"
    )
    watched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'watched_movies'
        verbose_name = 'İzlenen Film'
        verbose_name_plural = 'İzlenen Filmler'
        unique_together = ['user', 'movie']
        ordering = ['-watched_at']
    
    def __str__(self):
        status = "❤️" if self.liked else "👎"
        return f"{self.user.username} {status} {self.movie.title}"