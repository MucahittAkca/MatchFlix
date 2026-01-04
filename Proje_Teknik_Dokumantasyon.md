# MatchFlix - Akıllı Film Öneri ve Sosyal Platform
## Teknik Dokümantasyon

---

## 1. VERİTABANI MİMARİSİ

### Veritabanı Şeması

#### **1. Users Tablosu** (Django AbstractUser'dan extend)
```
users
├── id (PK)
├── username (UNIQUE, indexed)
├── email (UNIQUE, indexed)
├── password (hashed)
├── first_name
├── last_name
├── bio (TEXT) - Kullanıcı biyografisi
├── profile_picture (ImageField) - Profil fotoğrafı
├── date_of_birth
├── total_movies_watched (cached) - İzlenen film sayısı
├── avg_rating (Decimal) - Ortalama puan (0-10)
├── created_at
├── updated_at
└── Django Default Fields: is_active, is_staff, is_superuser, last_login
```

#### **2. Genres Tablosu** (Film Türleri)
```
genres
├── id (PK)
├── tmdb_id (UNIQUE, indexed) - TMDB API ID'si
├── name (CharField) - İngilizce adı
├── name_tr (CharField, nullable) - Türkçe adı
└── created_at
```

#### **3. Persons Tablosu** (Oyuncular, Yönetmenler, vb.)
```
persons
├── id (PK)
├── tmdb_id (UNIQUE, indexed)
├── name (CharField, indexed) - Kişi adı
├── profile_path (CharField, nullable) - Profil fotoğrafı URL
├── biography (TextField)
├── birthday (DateField)
├── deathday (DateField, nullable)
├── place_of_birth (CharField)
├── known_for_department (CharField) - Acting, Directing, Writing vb.
├── gender (IntegerField) - 0: Belirtilmemiş, 1: Kadın, 2: Erkek, 3: Diğer
├── popularity (FloatField) - TMDB popularite skoru
├── created_at
└── updated_at
```

#### **4. Movies Tablosu** (Ana Film Tablosu)
```
movies
├── id (PK)
├── tmdb_id (UNIQUE, indexed)
├── imdb_id (CharField, nullable)
├── title (CharField, indexed)
├── original_title (CharField)
├── overview (TextField)
├── tagline (CharField)
├── poster_path (CharField, nullable)
├── backdrop_path (CharField, nullable)
├── release_date (DateField, indexed)
├── runtime (IntegerField) - Dakika cinsinden
├── vote_average (FloatField, indexed) - 0-10 arası, TMDB puanı
├── vote_count (IntegerField)
├── popularity (FloatField, indexed)
├── original_language (CharField)
├── status (CharField) - rumored, planned, in_production, post_production, released, canceled
├── adult (BooleanField)
├── budget (BigIntegerField) - USD cinsinden
├── revenue (BigIntegerField) - USD cinsinden
├── homepage (URLField, nullable)
├── genres (ManyToManyField → Genres)
├── created_at
└── updated_at
```

#### **5. MovieCast Tablosu** (Film-Oyuncu İlişkisi)
```
movie_cast
├── id (PK)
├── movie_id (FK → movies, indexed)
├── person_id (FK → persons, indexed)
├── character_name (CharField) - Oynadığı karakter adı
├── cast_order (IntegerField) - Oyuncu sırası
└── created_at
```

#### **6. MovieCrew Tablosu** (Film-Ekip İlişkisi)
```
movie_crew
├── id (PK)
├── movie_id (FK → movies, indexed)
├── person_id (FK → persons, indexed)
├── department (CharField) - Directing, Writing, Cinematography vb.
├── job (CharField) - Director, Writer, Cinematographer vb.
└── created_at
```

#### **7. Ratings Tablosu** (Kullanıcı Puanları) - *Planlanmış*
```
ratings
├── id (PK)
├── user_id (FK → users, indexed)
├── movie_id (FK → movies, indexed)
├── score (IntegerField) - 1-10 arası puan
├── review (TextField, nullable) - Yorum metni
├── created_at
├── updated_at
└── unique_together(user_id, movie_id) - Aynı kullanıcı bir filme sadece bir puan verebilir
```

#### **8. Friendships Tablosu** (Arkadaş İlişkileri) - *Planlanmış*
```
friendships
├── id (PK)
├── user_id (FK → users, indexed) - İstek gönderen
├── friend_id (FK → users, indexed) - İstek alan
├── status (CharField) - pending, accepted, blocked
├── created_at
├── updated_at
└── unique_together(user_id, friend_id) - Çift yönlü ilişki yok
```

#### **9. Compatibility Scores Tablosu** (Uyumluluk Puanları) - *Planlanmış*
```
compatibility_scores
├── id (PK)
├── user_1_id (FK → users, indexed)
├── user_2_id (FK → users, indexed)
├── score (IntegerField) - 0-100 arası uyumluluk skoru
├── common_movies (IntegerField) - Ortak izlenen film sayısı
├── similar_genres (JSONField) - Benzer türler
├── similar_actors (JSONField) - Benzer oyuncular
├── similar_directors (JSONField) - Benzer yönetmenler
├── calculated_at (DateTimeField)
└── unique_together(user_1_id, user_2_id)
```

#### **10. Notifications Tablosu** (Bildirimler) - *Planlanmış*
```
notifications
├── id (PK)
├── user_id (FK → users, indexed)
├── movie_id (FK → movies, nullable)
├── notification_type (CharField) - new_movie, movie_release, friend_request vb.
├── title (CharField)
├── message (TextField)
├── is_read (BooleanField)
├── created_at
└── sent_at (DateTimeField, nullable)
```

#### **11. UserTasteProfile Tablosu** (Kullanıcı Tarz Profili) - *Planlanmış*
```
user_taste_profiles
├── id (PK)
├── user_id (FK → users, UNIQUE, indexed)
├── favorite_genres (JSONField) - {genre_id: weight, ...}
├── favorite_actors (JSONField) - [person_id, ...]
├── favorite_directors (JSONField) - [person_id, ...]
├── preferred_decades (JSONField) - {decade: weight, ...}
├── preferred_runtime (JSONField) - {short: 0.2, medium: 0.6, long: 0.2}
├── rating_style (CharField) - generous, balanced, harsh
├── average_rating (DecimalField) - Kullanıcının ortalama puanı
├── total_rated_movies (IntegerField)
├── onboarding_completed (BooleanField) - İlk seçim yapıldı mı
├── created_at
└── updated_at
```

#### **12. UserOnboardingSelection Tablosu** (Kayıt Sonrası Seçimler) - *Planlanmış*
```
user_onboarding_selections
├── id (PK)
├── user_id (FK → users, indexed)
├── movie_id (FK → movies, indexed)
├── selection_type (CharField) - liked, disliked, not_watched
├── created_at
└── unique_together(user_id, movie_id)
```

#### **13. QuickRecommendationSession Tablosu** (Hızlı Öneri Oturumları) - *Planlanmış*
```
quick_recommendation_sessions
├── id (PK)
├── user_id (FK → users, indexed)
├── session_type (CharField) - single, duo
├── partner_user_id (FK → users, nullable) - İki kişilik mod için
├── mood (CharField) - happy, emotional, excited, thoughtful, relaxed
├── time_available (CharField) - short, medium, long
├── era_preference (CharField) - recent, 2010s, classic
├── genre_preference (FK → genres, nullable)
├── recommendations (JSONField) - [movie_id, ...]
├── selected_movie_id (FK → movies, nullable) - Seçilen film
├── created_at
└── completed_at (DateTimeField, nullable)
```

---

## 2. API ŞEMALARI

### Base URL
```
http://localhost:8000/api
```

### Mevcut Endpoints

#### **Film Endpoints**

**1. Film Listesi (Filtreleme, Arama, Sıralama)**
```http
GET /api/movies/?page=1&limit=20&genre=28&rating_gte=7.0&year_gte=2020
```

**Parametreler:**
- `page` (int): Sayfa numarası
- `limit` (int): Sayfa başına film sayısı
- `genre` (int): Genre TMDB ID'si
- `rating_gte` (float): Minimum puan
- `rating_lte` (float): Maksimum puan
- `year_gte` (int): Başlangıç yılı
- `year_lte` (int): Bitiş yılı
- `original_language` (str): Dil kodu
- `adult` (bool): Yetişkin filmleri dahil et
- `search` (str): Başlık arama

**Cevap:**
```json
{
  "count": 5432,
  "next": "http://localhost:8000/api/movies/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "tmdb_id": 550,
      "title": "Fight Club",
      "original_title": "Fight Club",
      "poster_url": "https://image.tmdb.org/t/p/w500/...",
      "backdrop_url": "https://image.tmdb.org/t/p/w1280/...",
      "vote_average": 8.8,
      "vote_count": 24500,
      "release_date": "1999-10-15",
      "popularity": 85.5,
      "genres": [18, 28],
      "year": 1999
    }
  ]
}
```

**2. Film Detayı**
```http
GET /api/movies/550/
```

**Cevap:**
```json
{
  "id": 1,
  "tmdb_id": 550,
  "title": "Fight Club",
  "original_title": "Fight Club",
  "overview": "An insomniac office worker and a devil-may-care soapmaker form an underground fight club...",
  "tagline": "Lose yourself",
  "poster_url": "https://image.tmdb.org/t/p/w500/...",
  "backdrop_url": "https://image.tmdb.org/t/p/w1280/...",
  "release_date": "1999-10-15",
  "runtime": 139,
  "vote_average": 8.8,
  "vote_count": 24500,
  "popularity": 85.5,
  "original_language": "en",
  "status": "released",
  "adult": false,
  "budget": 63000000,
  "revenue": 100853753,
  "homepage": "https://www.fightclub.movie",
  "year": 1999,
  "genres": [
    {
      "id": 1,
      "tmdb_id": 18,
      "name": "Drama",
      "name_tr": "Dram"
    },
    {
      "id": 2,
      "tmdb_id": 28,
      "name": "Action",
      "name_tr": "Aksiyon"
    }
  ],
  "cast": [
    {
      "id": 1,
      "tmdb_id": 287,
      "name": "Brad Pitt",
      "character_name": "Tyler Durden",
      "cast_order": 1,
      "profile_url": "https://image.tmdb.org/t/p/w185/..."
    },
    {
      "id": 2,
      "tmdb_id": 500,
      "name": "Edward Norton",
      "character_name": "The Narrator",
      "cast_order": 2,
      "profile_url": "https://image.tmdb.org/t/p/w185/..."
    }
  ],
  "crew": [
    {
      "id": 1,
      "tmdb_id": 561,
      "name": "David Fincher",
      "department": "Directing",
      "job": "Director",
      "profile_url": "https://image.tmdb.org/t/p/w185/..."
    },
    {
      "id": 2,
      "tmdb_id": 5064,
      "name": "Jim Uhls",
      "department": "Writing",
      "job": "Screenplay",
      "profile_url": null
    }
  ]
}
```

**3. Film Arama**
```http
GET /api/movies/search/?q=inception
```

**Cevap:**
```json
{
  "results": [
    {
      "id": 27205,
      "tmdb_id": 27205,
      "title": "Inception",
      "poster_url": "https://image.tmdb.org/t/p/w500/...",
      "vote_average": 8.8,
      "release_date": "2010-07-16",
      "year": 2010,
      "genres": [28, 12, 878]
    }
  ]
}
```

**4. Popüler Filmler**
```http
GET /api/movies/popular/?page=1&limit=20
```

**5. Trend Filmler**
```http
GET /api/movies/trending/?time_window=week
```

**6. Vizyona Girecek Filmler**
```http
GET /api/movies/upcoming/?page=1
```

**7. En İyi Puanlanan Filmler**
```http
GET /api/movies/top_rated/?page=1
```

**8. Türe Göre Filmler**
```http
GET /api/movies/by_genre/?genre_id=28&page=1
```

**9. Benzer Filmler**
```http
GET /api/movies/550/similar/
```

#### **Tür Endpoints**

**1. Türlerin Listesi**
```http
GET /api/genres/
```

**Cevap:**
```json
{
  "count": 20,
  "results": [
    {
      "id": 1,
      "tmdb_id": 28,
      "name": "Action",
      "name_tr": "Aksiyon"
    },
    {
      "id": 2,
      "tmdb_id": 12,
      "name": "Adventure",
      "name_tr": "Macera"
    },
    {
      "id": 3,
      "tmdb_id": 16,
      "name": "Animation",
      "name_tr": "Animasyon"
    }
  ]
}
```

#### **Kişi Endpoints**

**1. Kişi Listesi**
```http
GET /api/persons/?search=brad&ordering=-popularity
```

**2. Kişi Detayı**
```http
GET /api/persons/287/
```

**Cevap:**
```json
{
  "id": 287,
  "tmdb_id": 287,
  "name": "Brad Pitt",
  "biography": "William Bradley Pitt is an American actor and film producer...",
  "birthday": "1963-12-18",
  "deathday": null,
  "place_of_birth": "Springfield, Missouri, USA",
  "known_for_department": "Acting",
  "gender": 2,
  "gender_display": "Erkek",
  "popularity": 92.5,
  "profile_url": "https://image.tmdb.org/t/p/w185/..."
}
```

---

## 3. UYGULAMA AKIŞLARI

### Senaryo 1: Film Arama
```
Kullanıcı: "Inception" yazıyor
        ↓
Frontend: GET /api/movies/search/?q=Inception
        ↓
Backend İşlemi:
  1. Veritabanında "Inception" ara
  2. Sonuç bulunursa döndür
  3. Sonuç bulunamazsa TMDB API'sine sor
  4. Bulduğu filmi veritabanına kaydet
        ↓
Sonuçlar kullanıcıya gösterilir
        ↓
Kullanıcı filme tıklar → Detay sayfası açılır
```

### Senaryo 2: Kategoriye Tıklama
```
Kullanıcı: "Aksiyon" kategorisine tıklıyor
        ↓
Frontend: GET /api/movies/by_genre/?genre_id=28&page=1
        ↓
Backend İşlemi:
  1. Veritabanında Aksiyon filmlerini ara
  2. Sayfala (20 film/sayfa)
  3. Hemen döndür (cache'li, çok hızlı)
        ↓
Anında sonuçlar gösterilir (0.5 saniye)
```

### Senaryo 3: Anasayfa Yükleme
```
Kullanıcı: Website açıyor
        ↓
Frontend: Aynı anda 3 istek
  - GET /api/movies/popular/?limit=10
  - GET /api/movies/trending/?limit=10
  - GET /api/genres/
        ↓
Backend: Veritabanından cache'li sonuçları döndür
        ↓
Sayfa hemen yüklenir (2-3 saniye)
        ↓
Kullanıcı filmleri görebilir ve interakt edebilir
```

### Senaryo 4: Kullanıcı Onboarding (Planlanmış)
```
Kullanıcı: Kayıt olduktan sonra
        ↓
Sistem: Onboarding ekranına yönlendir
        ↓
Adım 1: "Hoş geldin! Film zevkini öğrenmek istiyoruz"
        ↓
Adım 2: Popüler filmler grid/swipe ile gösterilir
        ↓
Kullanıcı: Her film için seçim yapar
  - 👍 İzledim & Beğendim
  - 👎 İzledim & Beğenmedim  
  - ⏭️ İzlemedim/Atla
        ↓
Backend İşlemi:
  1. Seçimleri user_onboarding_selections'a kaydet
  2. Tarz profilini hesapla (genre ağırlıkları, oyuncu/yönetmen tercihleri)
  3. user_taste_profiles tablosuna kaydet
  4. onboarding_completed = True yap
        ↓
Kullanıcı: Ana sayfaya yönlendirilir
        ↓
"Sizin İçin Özel" bölümü tarz profiline göre doldurulur
```

### Senaryo 5: Hızlı Öneri - Tek Kişi (Planlanmış)
```
Kullanıcı: "Hızlı Öneri" butonuna tıklar
        ↓
Sistem: Modal/Sayfa açılır
        ↓
Soru 1: "Bugün nasıl hissediyorsun?"
  😊 Mutlu → 😢 Duygusal → 😱 Heyecanlı → 🤔 Düşünceli → 😴 Rahat
        ↓
Soru 2: "Ne kadar zamanın var?"
  ⏱️ <90dk → ⏱️ 90-120dk → ⏱️ 120+dk
        ↓
Soru 3: "Yeni mi klasik mi?"
  🆕 Son 5 yıl → 📅 2010-2020 → 🎬 Klasikler
        ↓
Soru 4 (opsiyonel): "Belirli bir tür?"
  Tür seçimi veya "Fark etmez"
        ↓
Backend İşlemi:
  1. Kullanıcının tarz profilini al
  2. Cevaplara göre filtre oluştur:
     - mood → genre mapping
     - time → runtime filtresi
     - era → year filtresi
  3. Kullanıcının izlemediği filmleri bul
  4. Profil + filtre skoru hesapla
  5. Top 5 öneri döndür
        ↓
Sonuç: 5 film kartı gösterilir
        ↓
Kullanıcı: Birini seçer veya "Başka öner" der
```

### Senaryo 6: Uyumluluk Kontrolü (Planlanmış)
```
Kullanıcı_A: Kullanıcı_B'nin profiline gider
        ↓
Sistem: Uyumluluk skoru hesapla
        ↓
Backend İşlemi:
  1. Her iki kullanıcının tarz profilini al
  2. Ortak izlenen filmleri bul
  3. Bu filmlerde verdikleri puanları karşılaştır
  4. Tür tercihlerinin kosinüs benzerliğini hesapla
  5. Favori oyuncu/yönetmen kesişimini bul
  6. Ağırlıklı skor hesapla:
     - Ortak filmler: %40
     - Tür benzerliği: %30
     - Kişi benzerliği: %20
     - Puan stili: %10
        ↓
Sonuç: "%78 Uyumlusunuz!" + "Birlikte izleyebileceğiniz filmler"
```

---

## 4. PROJE DURUM RAPORU

### ✅ Tamamlanan Özellikler (%85)

**Backend & Altyapı:**
- **Models:** Movie, Genre, Person, MovieCast, MovieCrew, Rating, Watchlist, Friendship tamamlandı
- **API Endpoints:** Film listesi, detay, arama, popüler, trending, upcoming, by_genre
- **Film Veri Senkronizasyonu:** sync_genres, sync_popular_movies, sync_all_movies, fix_movie_translations
- **TMDB Entegrasyonu:** TMDBService class + Dil Fallback mekanizması

**Kullanıcı Sistemi:**
- **User System:** Registration, Login, Profile, Edit Profile tamamlandı
- **Rating System:** Film puanlama sistemi aktif
- **Watchlist System:** İzleme listesi ekleme/çıkarma aktif
- **Friendship System:** Arkadaş ekleme, kabul etme, reddetme aktif

**Frontend (Django Templates):**
- Ana sayfa (öneriler, trendler, yakında vizyona girecekler)
- Film detay sayfası (puanlama, watchlist, yorumlar)
- Keşfet sayfası (live search, hybrid search - lokal + TMDB)
- Profil sayfası (ayarlar, tema, dil)
- Arkadaşlar sayfası (arama, istek gönder/kabul/reddet)
- İzleme listesi sayfası
- Dark/Light Mode + Türkçe/İngilizce dil desteği
- Toast Notification sistemi

### 🔄 Devam Eden Özellikler (%10)

- **Kullanıcı Onboarding:** Kayıt sonrası film seçimi ekranı
- **Tarz Profili:** Kullanıcı tercihlerinin analizi ve kaydı
- **Hızlı Öneri (Tek Kişi):** Sorulu öneri sistemi
- **Uyumluluk Algoritması:** İki kullanıcı arasında score hesaplama
- **Quick Match (İki Kişi):** Ortak film önerisi

### ❌ Eksik Özellikler (%5)

- **Bildirim Sistemi:** Celery tasks ve e-mail bildirimleri
- **Grup Önerisi:** 3-4 kişilik gruplar için öneri
- **JustWatch API:** Film platform bilgisi
- **Test:** Pytest yazılmamış
- **Production Deploy:** Docker, CI/CD

---

## 5. TEKNOLOJI YIĞINI

### Backend
- **Django 5.0** - Web framework
- **Django REST Framework** - API development
- **PostgreSQL/SQLite** - Veritabanı
- **Redis** - Cache
- **Celery** - Task queue (planlanmış)

### Frontend (Planlanmış)
- **Django Templates** veya **React.js**
- **Tailwind CSS** - Styling

### Harici API'ler
- **TMDB API** - Film verileri
- **JustWatch API** - Platform bilgisi (planlanmış)

---

## 6. KURULUM VE ÇALIŞMA

### Management Commands
```bash
# Tüm kategorilerden film çek
python manage.py sync_all_movies --pages 10

# Sadece popüler filmler
python manage.py sync_all_movies --category popular --pages 5

# Türleri senkronize et
python manage.py sync_genres

# Django dev sunucusunu başlat
python manage.py runserver
```

### API Swagger Dokümantasyonu
```
http://localhost:8000/api/schema/swagger/
http://localhost:8000/api/schema/redoc/
```
