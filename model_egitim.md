# MatchFlix - Öneri Sistemi Model Eğitimi

## 📋 Genel Bakış

Bu döküman, MatchFlix için hibrit öneri sisteminin nasıl kurulacağını açıklar.
MovieLens veri seti + Content-Based filtering kombinasyonu kullanılacaktır.

---

## 🏗️ Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────┐
│                    MatchFlix Öneri Sistemi                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│   │  Content    │    │ Collaborative│    │   Hibrit    │    │
│   │   Based     │ +  │  Filtering   │ =  │   Skor      │    │
│   │  (TMDB)     │    │ (MovieLens)  │    │             │    │
│   └─────────────┘    └─────────────┘    └─────────────┘    │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│   Film Benzerliği    Kullanıcı Benzerliği   Final Öneri    │
│   (tür, oyuncu,      (SVD latent factors)                  │
│    yönetmen)                                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 MovieLens Veri Seti

### İndir
- **URL:** https://grouplens.org/datasets/movielens/
- **Versiyon:** MovieLens 25M (Önerilen)
- **Boyut:** ~250MB (sıkıştırılmış)

### Dosya İçeriği
```
ml-25m/
├── movies.csv      → movieId, title, genres
├── ratings.csv     → userId, movieId, rating, timestamp (25M satır!)
├── links.csv       → movieId, imdbId, tmdbId  ← ÖNEMLİ!
├── tags.csv        → Kullanıcı etiketleri
└── genome-*        → Tag genome verileri
```

### TMDB Eşleştirme
`links.csv` dosyasında her filmin TMDB ID'si var:
```csv
movieId,imdbId,tmdbId
1,0114709,862
2,0113497,8844
3,0113228,15602
```

Bu sayede MovieLens filmlerini bizim veritabanımızdaki filmlerle eşleştirebiliriz.

---

## 🔧 Gerekli Kütüphaneler

```bash
pip install scikit-surprise pandas numpy scipy
```

`requirements.txt` eklemeleri:
```
scikit-surprise==1.1.3
scipy>=1.11.0
```

---

## 📁 Dosya Yapısı

```
apps/
└── recommendations/
    ├── __init__.py
    ├── models.py              # UserTasteProfile, RecommendationLog
    ├── services.py            # HybridRecommender class
    ├── utils.py               # Yardımcı fonksiyonlar
    ├── content_based.py       # Content-Based algoritma
    ├── collaborative.py       # Collaborative Filtering (SVD)
    └── management/
        └── commands/
            ├── import_movielens.py   # MovieLens veri import
            ├── train_model.py        # SVD model eğitimi
            └── update_profiles.py    # Kullanıcı profil güncelleme
```

---

## 🗄️ Veritabanı Modelleri

### UserTasteProfile
```python
class UserTasteProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='taste_profile')
    
    # Tür tercihleri (JSON)
    genre_weights = models.JSONField(default=dict)
    # Örnek: {"28": 0.8, "12": 0.6, "35": 0.3}  # Action, Adventure, Comedy
    
    # Favori kişiler
    favorite_actors = models.JSONField(default=list)      # [person_id, ...]
    favorite_directors = models.JSONField(default=list)   # [person_id, ...]
    
    # Tercih edilen dönemler
    preferred_decades = models.JSONField(default=dict)
    # Örnek: {"2020s": 0.5, "2010s": 0.3, "2000s": 0.2}
    
    # Puan verme stili
    rating_style = models.CharField(max_length=20, default='balanced')
    # 'generous' (yüksek puanlar), 'balanced', 'harsh' (düşük puanlar)
    
    average_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    total_rated_movies = models.IntegerField(default=0)
    
    # Onboarding durumu
    onboarding_completed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### MovieLensMapping
```python
class MovieLensMapping(models.Model):
    """MovieLens ID - TMDB ID eşleştirmesi"""
    movielens_id = models.IntegerField(unique=True, db_index=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True)
    tmdb_id = models.IntegerField(db_index=True)
    imdb_id = models.CharField(max_length=20, null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['movielens_id']),
            models.Index(fields=['tmdb_id']),
        ]
```

### RecommendationLog
```python
class RecommendationLog(models.Model):
    """Öneri geçmişi (analiz için)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    
    recommendation_type = models.CharField(max_length=20)
    # 'content', 'collaborative', 'hybrid', 'quick_match'
    
    content_score = models.FloatField(null=True)
    collab_score = models.FloatField(null=True)
    final_score = models.FloatField()
    
    was_clicked = models.BooleanField(default=False)
    was_rated = models.BooleanField(default=False)
    rating_given = models.IntegerField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 🧠 Algoritma Implementasyonu

### 1. MovieLens Import
```python
# management/commands/import_movielens.py

import pandas as pd
from django.core.management.base import BaseCommand
from apps.movies.models import Movie
from apps.recommendations.models import MovieLensMapping

class Command(BaseCommand):
    help = 'Import MovieLens links.csv for TMDB mapping'
    
    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, required=True, 
                          help='Path to ml-25m folder')
    
    def handle(self, *args, **options):
        path = options['path']
        
        # links.csv oku
        links_df = pd.read_csv(f'{path}/links.csv')
        
        # Bizim DB'deki TMDB ID'leri
        our_tmdb_ids = set(Movie.objects.values_list('tmdb_id', flat=True))
        
        created = 0
        for _, row in links_df.iterrows():
            tmdb_id = row.get('tmdbId')
            if pd.isna(tmdb_id):
                continue
            
            tmdb_id = int(tmdb_id)
            
            # Eşleşen film var mı?
            movie = None
            if tmdb_id in our_tmdb_ids:
                movie = Movie.objects.filter(tmdb_id=tmdb_id).first()
            
            MovieLensMapping.objects.update_or_create(
                movielens_id=int(row['movieId']),
                defaults={
                    'tmdb_id': tmdb_id,
                    'movie': movie,
                    'imdb_id': str(row.get('imdbId', '')) if pd.notna(row.get('imdbId')) else None
                }
            )
            created += 1
        
        self.stdout.write(f'✅ {created} mapping oluşturuldu')
        
        matched = MovieLensMapping.objects.filter(movie__isnull=False).count()
        self.stdout.write(f'✅ {matched} film eşleştirildi')
```

### 2. SVD Model Eğitimi
```python
# management/commands/train_model.py

import pandas as pd
import pickle
from surprise import Dataset, Reader, SVD
from surprise.model_selection import cross_validate
from django.core.management.base import BaseCommand
from apps.recommendations.models import MovieLensMapping

class Command(BaseCommand):
    help = 'Train SVD recommendation model using MovieLens data'
    
    def add_arguments(self, parser):
        parser.add_argument('--ratings-path', type=str, required=True)
        parser.add_argument('--output', type=str, default='recommendation_model.pkl')
        parser.add_argument('--factors', type=int, default=150)
        parser.add_argument('--epochs', type=int, default=30)
    
    def handle(self, *args, **options):
        self.stdout.write('📊 MovieLens ratings yükleniyor...')
        
        # Ratings oku
        ratings_df = pd.read_csv(options['ratings_path'])
        self.stdout.write(f'   Toplam rating: {len(ratings_df):,}')
        
        # Sadece eşleşen filmleri al
        valid_ml_ids = set(
            MovieLensMapping.objects.filter(movie__isnull=False)
            .values_list('movielens_id', flat=True)
        )
        
        ratings_df = ratings_df[ratings_df['movieId'].isin(valid_ml_ids)]
        self.stdout.write(f'   Eşleşen rating: {len(ratings_df):,}')
        
        # Surprise formatına çevir
        reader = Reader(rating_scale=(0.5, 5.0))
        data = Dataset.load_from_df(
            ratings_df[['userId', 'movieId', 'rating']], 
            reader
        )
        
        # Model oluştur
        self.stdout.write('🧠 SVD modeli eğitiliyor...')
        model = SVD(
            n_factors=options['factors'],
            n_epochs=options['epochs'],
            lr_all=0.005,
            reg_all=0.02,
            verbose=True
        )
        
        # Cross-validation
        self.stdout.write('📈 Cross-validation...')
        cv_results = cross_validate(model, data, measures=['RMSE', 'MAE'], cv=3, verbose=True)
        
        self.stdout.write(f'   RMSE: {cv_results["test_rmse"].mean():.4f}')
        self.stdout.write(f'   MAE: {cv_results["test_mae"].mean():.4f}')
        
        # Full training
        self.stdout.write('🔄 Tam eğitim...')
        trainset = data.build_full_trainset()
        model.fit(trainset)
        
        # Kaydet
        output_path = options['output']
        with open(output_path, 'wb') as f:
            pickle.dump({
                'model': model,
                'n_factors': options['factors'],
                'rmse': cv_results["test_rmse"].mean(),
                'mae': cv_results["test_mae"].mean(),
            }, f)
        
        self.stdout.write(f'✅ Model kaydedildi: {output_path}')
```

### 3. Hibrit Öneri Servisi
```python
# services.py

import pickle
import numpy as np
from django.conf import settings
from sklearn.metrics.pairwise import cosine_similarity
from apps.movies.models import Movie, Rating
from apps.recommendations.models import MovieLensMapping, UserTasteProfile

# Mood → Genre eşleştirmesi
MOOD_GENRE_MAP = {
    'happy': ['Comedy', 'Animation', 'Family', 'Musical'],
    'emotional': ['Drama', 'Romance'],
    'excited': ['Action', 'Thriller', 'Adventure'],
    'thoughtful': ['Science Fiction', 'Documentary', 'Mystery'],
    'relaxed': ['Comedy', 'Animation', 'Family'],
}

class HybridRecommender:
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_model()
        return cls._instance
    
    def _load_model(self):
        """SVD modelini yükle"""
        try:
            model_path = getattr(settings, 'RECOMMENDATION_MODEL_PATH', 'recommendation_model.pkl')
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
                self._model = data['model']
                print(f"✅ Öneri modeli yüklendi (RMSE: {data['rmse']:.4f})")
        except FileNotFoundError:
            print("⚠️ Öneri modeli bulunamadı, sadece Content-Based kullanılacak")
            self._model = None
    
    def get_content_score(self, user_profile: UserTasteProfile, movie: Movie) -> float:
        """Film-kullanıcı içerik benzerliği (0-1)"""
        if not user_profile or not user_profile.genre_weights:
            return 0.5
        
        score = 0.0
        total_weight = sum(user_profile.genre_weights.values())
        
        if total_weight == 0:
            return 0.5
        
        # Tür benzerliği
        for genre in movie.genres.all():
            genre_weight = user_profile.genre_weights.get(str(genre.id), 0)
            score += genre_weight / total_weight
        
        # Favori yönetmen bonusu
        directors = movie.crew.filter(job='Director').values_list('person_id', flat=True)
        for d_id in directors:
            if d_id in user_profile.favorite_directors:
                score += 0.2
                break
        
        # Favori oyuncu bonusu
        actors = movie.cast.all()[:5].values_list('person_id', flat=True)
        for a_id in actors:
            if a_id in user_profile.favorite_actors:
                score += 0.1
        
        return min(score, 1.0)
    
    def get_collaborative_score(self, user_id: int, movie_id: int) -> float:
        """SVD tabanlı tahmin (0-1)"""
        if self._model is None:
            return 0.5
        
        try:
            # Movie → MovieLens ID
            mapping = MovieLensMapping.objects.filter(movie_id=movie_id).first()
            if not mapping:
                return 0.5
            
            # En benzer MovieLens kullanıcısını bul (basitleştirilmiş)
            # Gerçek implementasyonda kullanıcı eşleştirmesi yapılmalı
            ml_user_id = user_id  # Placeholder
            
            prediction = self._model.predict(ml_user_id, mapping.movielens_id)
            return prediction.est / 5.0  # 0-1 normalize
        except Exception:
            return 0.5
    
    def recommend(
        self, 
        user, 
        n: int = 10, 
        mood: str = None,
        time_available: str = None,
        era: str = None,
        genre_id: int = None
    ) -> list:
        """Hibrit öneri al"""
        
        # Kullanıcı profili
        try:
            profile = user.taste_profile
        except UserTasteProfile.DoesNotExist:
            profile = None
        
        # Ağırlıklar (cold start'a göre ayarla)
        if not profile or profile.total_rated_movies < 5:
            content_weight, collab_weight = 1.0, 0.0
        elif profile.total_rated_movies < 20:
            content_weight, collab_weight = 0.6, 0.4
        else:
            content_weight, collab_weight = 0.3, 0.7
        
        # İzlemediği filmler
        watched_ids = Rating.objects.filter(user=user).values_list('movie_id', flat=True)
        candidates = Movie.objects.exclude(id__in=watched_ids)
        
        # Filtreler
        if mood and mood in MOOD_GENRE_MAP:
            candidates = candidates.filter(genres__name__in=MOOD_GENRE_MAP[mood])
        
        if time_available == 'short':
            candidates = candidates.filter(runtime__lt=90)
        elif time_available == 'medium':
            candidates = candidates.filter(runtime__gte=90, runtime__lte=120)
        elif time_available == 'long':
            candidates = candidates.filter(runtime__gt=120)
        
        if era == 'recent':
            candidates = candidates.filter(release_date__year__gte=2020)
        elif era == '2010s':
            candidates = candidates.filter(release_date__year__gte=2010, release_date__year__lt=2020)
        elif era == 'classic':
            candidates = candidates.filter(release_date__year__lt=2010)
        
        if genre_id:
            candidates = candidates.filter(genres__id=genre_id)
        
        # Skor hesapla
        scored = []
        for movie in candidates.distinct()[:500]:  # Performans limiti
            content = self.get_content_score(profile, movie)
            collab = self.get_collaborative_score(user.id, movie.id)
            
            final = (content_weight * content) + (collab_weight * collab)
            
            # TMDB bonus
            if movie.vote_average:
                final += (movie.vote_average / 10) * 0.1
            
            scored.append((movie, final, content, collab))
        
        # Sırala
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored[:n]
    
    def calculate_compatibility(self, user_a, user_b) -> dict:
        """İki kullanıcı arasında uyumluluk skoru"""
        
        try:
            profile_a = user_a.taste_profile
            profile_b = user_b.taste_profile
        except UserTasteProfile.DoesNotExist:
            return {'score': 50, 'common_movies': 0, 'message': 'Yeterli veri yok'}
        
        # 1. Tür benzerliği
        all_genres = set(profile_a.genre_weights.keys()) | set(profile_b.genre_weights.keys())
        if all_genres:
            vec_a = [profile_a.genre_weights.get(g, 0) for g in all_genres]
            vec_b = [profile_b.genre_weights.get(g, 0) for g in all_genres]
            genre_sim = cosine_similarity([vec_a], [vec_b])[0][0]
        else:
            genre_sim = 0.5
        
        # 2. Ortak izlenen filmler
        ratings_a = set(Rating.objects.filter(user=user_a).values_list('movie_id', flat=True))
        ratings_b = set(Rating.objects.filter(user=user_b).values_list('movie_id', flat=True))
        common_movies = ratings_a & ratings_b
        
        if common_movies:
            # Puan benzerliği
            diffs = []
            for movie_id in common_movies:
                r_a = Rating.objects.get(user=user_a, movie_id=movie_id).score
                r_b = Rating.objects.get(user=user_b, movie_id=movie_id).score
                diffs.append(abs(r_a - r_b))
            
            rating_sim = 1 - (sum(diffs) / len(diffs) / 10)
        else:
            rating_sim = 0.5
        
        # 3. Favori kişi benzerliği
        common_actors = set(profile_a.favorite_actors) & set(profile_b.favorite_actors)
        common_directors = set(profile_a.favorite_directors) & set(profile_b.favorite_directors)
        person_sim = min((len(common_actors) + len(common_directors) * 2) / 10, 1.0)
        
        # Final skor
        final_score = (genre_sim * 0.4) + (rating_sim * 0.4) + (person_sim * 0.2)
        
        return {
            'score': int(final_score * 100),
            'common_movies': len(common_movies),
            'genre_similarity': int(genre_sim * 100),
            'rating_similarity': int(rating_sim * 100),
            'common_actors': len(common_actors),
            'common_directors': len(common_directors),
        }
    
    def get_movies_for_both(self, user_a, user_b, n: int = 10) -> list:
        """İki kullanıcı için ortak film önerileri"""
        
        # Her iki kullanıcının da izlemediği filmler
        watched_a = set(Rating.objects.filter(user=user_a).values_list('movie_id', flat=True))
        watched_b = set(Rating.objects.filter(user=user_b).values_list('movie_id', flat=True))
        watched_both = watched_a | watched_b
        
        candidates = Movie.objects.exclude(id__in=watched_both)
        
        # Her filme her iki kullanıcı için skor hesapla
        scored = []
        for movie in candidates[:300]:
            score_a = self.get_content_score(user_a.taste_profile, movie)
            score_b = self.get_content_score(user_b.taste_profile, movie)
            
            # Ortalama değil, minimum skoru al (her ikisinin de sevmesi gerekiyor)
            combined = min(score_a, score_b)
            
            # TMDB bonus
            if movie.vote_average:
                combined += (movie.vote_average / 10) * 0.1
            
            scored.append((movie, combined, score_a, score_b))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:n]
```

---

## 🚀 Kullanım

### Model Eğitimi (Bir kere yapılır)
```bash
# 1. MovieLens indir ve çıkar
wget https://files.grouplens.org/datasets/movielens/ml-25m.zip
unzip ml-25m.zip

# 2. Mapping import
python manage.py import_movielens --path ./ml-25m

# 3. Model eğit
python manage.py train_model --ratings-path ./ml-25m/ratings.csv --output recommendation_model.pkl
```

### View'da Kullanım
```python
from apps.recommendations.services import HybridRecommender

def quick_recommendation(request):
    recommender = HybridRecommender()
    
    recommendations = recommender.recommend(
        user=request.user,
        n=10,
        mood=request.GET.get('mood'),
        time_available=request.GET.get('time'),
        era=request.GET.get('era'),
    )
    
    return render(request, 'recommendations.html', {
        'recommendations': recommendations
    })

def compatibility_view(request, friend_id):
    recommender = HybridRecommender()
    friend = User.objects.get(id=friend_id)
    
    result = recommender.calculate_compatibility(request.user, friend)
    common_movies = recommender.get_movies_for_both(request.user, friend)
    
    return render(request, 'compatibility.html', {
        'friend': friend,
        'compatibility': result,
        'common_recommendations': common_movies,
    })
```

---

## 📈 Performans Metrikleri

### Hedefler
| Metrik | Hedef | Açıklama |
|--------|-------|----------|
| RMSE | < 0.90 | Root Mean Square Error |
| MAE | < 0.70 | Mean Absolute Error |
| Öneri süresi | < 500ms | 10 film önerisi |
| Cold start | < 5 film | Yeni kullanıcı için minimum veri |

### İzleme
- `RecommendationLog` tablosunda click-through rate takibi
- A/B testing için farklı ağırlık kombinasyonları
- Kullanıcı memnuniyet anketi

---

## ⏱️ Tahmini Süre

| Görev | Süre |
|-------|------|
| MovieLens indirme & çıkarma | 30 dk |
| Mapping import | 30 dk |
| SVD model eğitimi | 2-3 saat |
| HybridRecommender test | 1 saat |
| **Toplam** | **4-5 saat** |

---

## 📝 Notlar

1. **Model güncellemesi:** Ayda bir yeniden eğitim önerilir
2. **Yeni filmler:** TMDB'den eklenen yeni filmler otomatik content-based'e dahil olur
3. **Ölçekleme:** 10K+ kullanıcıda Redis cache eklenebilir
4. **Alternatif:** LightFM, Implicit kütüphaneleri de değerlendirilebilir

---

**Hazırlayan:** MatchFlix Geliştirme Ekibi  
**Son Güncelleme:** 29 Aralık 2025  
**Durum:** Beklemede (Diğer özellikler tamamlandıktan sonra implement edilecek)

