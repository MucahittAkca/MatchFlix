# MatchFlix - Akıllı Film Öneri ve Sosyal Platform

## Bitirme Projesi - Güncellenmiş Dokümantasyon

---

## 1. KONUNUN ÖNEMİ VE ÖZGÜN DEĞERİ

Günümüzde dijital platformlarda film izlemek hayatımızın bir parçası haline geldi. Netflix, Amazon Prime, Disney+ gibi onlarca platform var ve her birinde binlerce film bulunuyor. Ancak insanlar "Bu akşam ne izlesek?" sorusuna cevap bulmakta zorlanıyor. Özellikle arkadaşlarla veya sevgiliyle ortak bir film seçmek gerçek bir sorun haline gelmiş durumda.

Mevcut öneri sistemleri (Netflix, IMDb) genellikle kişisel tercihlerinizi analiz ediyor ama sosyal boyutu göz ardı ediyor. **İki kişinin ortak zevklerini analiz edip "sizin ikinize de uygun" bir film öneren kapsamlı bir platform şu an piyasada yok.**

MatchFlix projesi, bu soruna çözüm getirerek kullanıcıların hem kendi zevklerini keşfetmelerini hem de sosyal çevresiyle uyumlu filmler bulmalarını sağlayacak. Bu proje, gerçek bir ihtiyacı karşılayan, günlük hayatta aktif kullanılabilecek sosyal bir film platformu olmayı hedefliyor.

**Projenin Özgün Değeri:**
- İki kullanıcı arasında film zevki uyumluluğu analizi (%0-100 skoru)
- Hızlı karar mekanizması (Quick Match: her iki taraf 1 film seçer, sistem 3-5 öneri sunar)
- Vizyona girecek filmlerin kullanıcı zevkine göre otomatik takibi ve bildirim sistemi
- Grup izleme önerileri (3-4 kişilik arkadaş grupları için)
- Content-based ve Collaborative Filtering algoritmaları ile kişiselleştirilmiş öneriler

---

## 2. ARAŞTIRMA SORULARI İLE AMAÇ VE HEDEFLER

### Araştırma Soruları

1. **Kullanıcı Profili:** Kullanıcıların film izleme alışkanlıklarını ve tercihlerini nasıl daha doğru analiz edebiliriz?
2. **Uyumluluk Analizi:** İki farklı kullanıcının film zevklerini karşılaştırıp uyumluluk skorunu hesaplamak için hangi parametreler kullanılmalı?
3. **Vizyon Eşleştirmesi:** Vizyona girecek filmlerin kullanıcı tercihleriyle eşleştirilmesi için nasıl bir algoritma tasarlanabilir?
4. **Kalite Metriği:** Kullanıcılara gönderilen önerilerin doğruluğunu ve memnuniyeti nasıl ölçebiliriz?
5. **Hızlı Karar Mekanizması:** Hızlı film seçimi için yapay zeka destekli öneri sistemi nasıl çalışmalı?

### Ana Amaç

Kullanıcıların film seçim sürecini kolaylaştıran, sosyal etkileşimi destekleyen ve **kişiselleştirilmiş öneriler** sunan bir web platformu geliştirmek.

### Spesifik Hedefler

#### 1. Kullanıcı Profil Analizi
- Her kullanıcı için film zevki profili oluşturmak (tür, yönetmen, oyuncu tercihleri)
- İzlenen filmlere göre otomatik tarz belirleme sistemi geliştirmek
- Minimum 50 parametreli detaylı analiz yapmak
- Kullanıcı puanlamalarına dayalı preference vector'ü hesaplamak

#### 2. Sosyal Etkileşim
- İki kullanıcı arasında %1-100 arası uyumluluk skoru hesaplamak
- Ortak izlenebilecek filmleri önceliklendirerek listelemek
- Arkadaş ekleme, izleme listesi paylaşma özelliklerini aktif hale getirmek
- Arkadaş isteği ve onaylama mekanizması oluşturmak

#### 3. Kullanıcı Onboarding & Tarz Profili
- Yeni kayıt olan kullanıcıya izlediği/beğendiği filmleri seçtirmek
- Seçilen filmlerden kullanıcının tarz profilini (genre, yönetmen, oyuncu tercihleri) otomatik oluşturmak
- Tarz profilini veritabanına kaydetmek ve güncel tutmak
- "Sizin İçin Özel" bölümünü bu profile göre doldurmak
- Kullanıcı yeni filmler izledikçe profili dinamik olarak güncellemek

#### 4. Hızlı Karar Mekanizması (Quick Match)
- **Tek Kişilik Mod:** Kullanıcıya sorular sorarak (mod, tür, süre vb.) kişiselleştirilmiş öneri sunmak
- **İki Kişilik Mod:** Her iki kullanıcı 1 film seçer, sistem 3-5 ortak öneri sunar
- Öneri algoritmasının 10 saniye altında sonuç vermesini sağlamak
- Önerilerin %80 üzeri kullanıcı memnuniyeti almasını hedeflemek

#### 4. Vizyon Takibi
- TMDB API üzerinden vizyona girecek filmleri günlük olarak otomatik çekmek
- Kullanıcının tarz profiliyle uyumlu filmleri tespit edip bildirim göndermek
- İki kullanıcının ortak ilgi alanına giren vizyon filmleri için "birlikte izleyin" önerisi sunmak
- Başlayan yeni dizilerin de takibini sağlamak

#### 5. Bildirim Sistemi
- E-posta ve platform içi bildirimler göndermek
- Kullanıcının belirlediği sıklıkta (günlük/haftalık) özet raporlar hazırlamak
- Spam'e düşmeden etkili bildirim stratejisi oluşturmak
- Bildirim tercihlerini yönetebilir hale getirmek

#### 6. Platform Altyapısı
- Minimum 10,000 film verisini yöneten veritabanı kurmak (Tamamlandı: 8,000+ film)
- Aynı anda 100+ kullanıcıya hizmet verebilecek performanslı backend geliştirmek
- Mobil uyumlu, kullanıcı dostu arayüz tasarlamak
- API yanıt sürelerini 200ms altında tutmak

---

## 3. YÖNTEM VE TEKNOLOJİLER

### Backend Mimarisi

#### Django REST Framework Kullanımı
- **RESTful API'ler** geliştirmek için DRF kullanıldı
- **ViewSet** ve **Router** ile otomatik URL routing
- **Serializers** ile request/response validasyonu
- **Permission Classes** ile kullanıcı yetkilendirmesi
- **Filtering ve Search** özellikleri entegre edildi

#### Veritabanı Tasarımı
- **PostgreSQL/SQLite** ile ilişkisel veri modeli
- **Indexed** sorgular için performans optimizasyonu
- **Many-to-Many** ilişkileri (Films ↔ Genres, Films ↔ Cast, Films ↔ Crew)
- Gelecek özellikler için **Ratings**, **Friendships**, **Compatibility_Scores** tablolarının şeması tasarlandı

#### Cache Mekanizması
- **Redis** ile sık sorgulanan verileri cache'leme
- Popüler filmler listesi cache'lenmekte
- Genre listesi cache'lenmekte
- Compatibility scores cache'lenmekte (planlanmış)

### Harici API Entegrasyonları

#### TMDB API
**Fonksiyonları:**
- Film detayları çekme (title, overview, cast, crew, budget, revenue vb.)
- Popüler filmler listeleme
- Trend filmler (weekly/daily)
- Vizyona girecek filmler
- En iyi puanlanan filmler
- Film arama
- Tür listesi
- Kişi detayları (oyuncular, yönetmenler)

**Entegrasyon:**
```python
# services.py'de TMDBService class ile merkezi yönetim
class TMDBService:
    - get_popular_movies(page)
    - get_trending_movies(time_window)
    - get_upcoming_movies(page)
    - get_top_rated_movies(page)
    - get_movie_details(tmdb_id)
    - search_movie(query, page)
    - get_genres()
    - get_person_details(person_id)
```

#### JustWatch API (Planlanmış)
- Filmlerin hangi platformda (Netflix, Prime, Disney+ vb.) bulunduğu
- Platformdaki kullanılabilirlik durumu
- Lisans bilgileri

### Veri Senkronizasyon

#### Management Commands
```bash
python manage.py sync_genres
  → TMDB'den tüm türleri çeker ve DB'ye kaydeder

python manage.py sync_popular_movies --pages 3
  → Popüler filmler ve detaylarını çeker

python manage.py sync_all_movies --pages 5
  → Popüler + Trending + Upcoming + Top Rated
  → 4 kategori × 5 sayfa × 20 film = 400 film
```

### Öneri Algoritması Mimarisi

#### 3.1 Content-Based Filtering
```
Kullanıcının izlediği filmleri analiz:
├── Türler (Action: 60%, Drama: 30%, Sci-Fi: 10%)
├── Yönetmenler (Tarantino, Nolan, Kubrick gibi)
├── Oyuncular (Tom Hanks, Leonardo DiCaprio gibi)
├── Yıl aralığı (1990-2020'ler tercihi)
└── Puan eğilimi (7+ puanlı filmler)

Sonra benzer özelliklere sahip yeni filmler öner
```

#### 3.2 Collaborative Filtering
```
Benzer puanlama yapan kullanıcıları bul:
├── User_A ve User_B'nin ortak filmlerini kontrol et
├── Aynı filmlere benzer puanlar verdilerse
└── User_A'nın sevdiği ama User_B'nin görmediği filmi öner

Scikit-learn ile:
  - Cosine Similarity matrisler
  - K-Nearest Neighbors (KNN)
  - Matrix Factorization (ileri aşama)
```

#### 3.3 Kullanıcı Onboarding & Tarz Profili Oluşturma
```
Kayıt Sonrası Akış:
├── Adım 1: Hoş Geldin Ekranı
│   └── "Film zevkini öğrenmek istiyoruz!"
├── Adım 2: Film Seçimi (Swipe/Grid)
│   ├── Popüler filmlerden 20-30 tanesi gösterilir
│   ├── Kullanıcı beğendiklerini seçer (min 5, max 20)
│   └── "İzledim & Beğendim" / "İzlemedim" / "İzledim & Beğenmedim"
├── Adım 3: Tür Tercihi (Opsiyonel)
│   └── Favori türlerini seçmesi istenir
└── Adım 4: Profil Oluşturma
    └── Sistem seçimlerden tarz profilini hesaplar

Tarz Profili Yapısı (user_taste_profile):
├── favorite_genres: {Action: 0.8, Drama: 0.6, Comedy: 0.3, ...}
├── favorite_actors: [id1, id2, id3, ...]
├── favorite_directors: [id1, id2, ...]
├── preferred_decades: {2020s: 0.5, 2010s: 0.3, ...}
├── preferred_runtime: {short: 0.2, medium: 0.6, long: 0.2}
├── rating_style: {average: 7.2, generous/harsh}
└── last_updated: timestamp

Dinamik Güncelleme:
- Kullanıcı her film puanladığında profil güncellenir
- Ağırlıklar: Son izlenenler > Eski izlenenler
- Decay factor ile eski tercihler zayıflar
```

#### 3.4 Hızlı Öneri Sistemi (Tek Kişilik Mod)
```
Akış:
├── Kullanıcı "Hızlı Öneri" butonuna tıklar
├── Soru 1: "Bugün nasıl hissediyorsun?"
│   ├── 😊 Mutlu/Enerjik → Komedi, Aksiyon
│   ├── 😢 Duygusal → Dram, Romantik
│   ├── 😱 Heyecanlı → Gerilim, Korku
│   ├── 🤔 Düşünceli → Bilim Kurgu, Belgesel
│   └── 😴 Rahat → Hafif komedi, Animasyon
├── Soru 2: "Ne kadar zamanın var?"
│   ├── ⏱️ 90 dk altı
│   ├── ⏱️ 90-120 dk
│   └── ⏱️ 120+ dk
├── Soru 3: "Yeni mi eski mi?"
│   ├── 🆕 Son 5 yıl
│   ├── 📅 2010-2020
│   └── 🎬 Klasikler
├── Soru 4 (Opsiyonel): "Belirli bir tür?"
│   └── Tür seçimi veya "Fark etmez"
└── Sonuç: 5 film önerisi (kullanıcı profiline + cevaplara göre)

Algoritma:
1. Kullanıcının tarz profilini al
2. Cevaplara göre filtre uygula (mood → genre, time → runtime, era → year)
3. Profil dışı tercih varsa keşif faktörü ekle
4. İzlemediği filmlerden skora göre sırala
5. Top 5 öneri sun
```

#### 3.5 Uyumluluk Skoru Hesaplama (İki Kullanıcı Arası)
```
Parametreler ve Ağırlıklar:
├── Ortak İzlenen Filmler (40%)
│   ├── Ortak film sayısı × 10
│   └── Bu filmlerde verilen puanlar ne kadar yakın
├── Benzer Türler (30%)
│   ├── Tür tercihlerinin kosinüs benzerliği
│   └── Örnek: User_A=Action 60%, User_B=Action 55% → yüksek score
├── Benzer Oyuncular/Yönetmenler (20%)
│   ├── En sevilen kişilerin benzerliği
│   └── Örnek: İkisi de Nolan hayranı → +puan
└── Puan Verme Eğilimi (10%)
    ├── User_A: orta 7.5 puan verir
    ├── User_B: orta 7.0 puan verir → benzer → +puan
    └── User_A: orta 9.5, User_B: orta 5.0 → farklı → -puan

Hesaplama:
score = (w1 × common_score) + (w2 × genre_score) + 
        (w3 × person_score) + (w4 × rating_style_score)

Sonuç: 0-100 arası uyumluluk puanı
```

### Bildirim Sistemi Mimarisi

#### Celery + Celery Beat
```python
# Zamanlanmış görevler
@periodic_task(run_every=crontab(hour=0, minute=0))
def check_upcoming_movies():
    """Her gün saat 00:00'da çalışır"""
    # Vizyona girecek filmleri kontrol et
    # Kullanıcı profileriyle eşleştir
    # Bildirim gönder

@periodic_task(run_every=crontab(hour=9, minute=0, day_of_week=1))
def send_weekly_recommendations():
    """Her Pazartesi saat 09:00'da çalışır"""
    # Haftanın önerileri hazırla
    # E-mail gönder
```

#### E-mail Backend
```
SendGrid / Amazon SES
├── Vizyona giren filmler bildirimi
├── Haftalık özet raporu
├── Yeni arkadaş isteği
├── Uyumluluk skoru güncelleme
└── Marketing emails (opsiyonel)
```

### Frontend Mimarisi (MVP)

#### Faz 1: Django Templates
- Django built-in template engine
- Bootstrap/Tailwind CSS styling
- AJAX requests için Fetch API
- Server-side rendering

#### Faz 2: React.js (Zaman Kalırsa)
- Component-based architecture
- State management (Redux/Context)
- Client-side routing
- Real-time updates (WebSocket)

### Test Stratejisi

#### Unit Tests (Pytest)
```python
test_models.py        # Model testleri
test_views.py         # View/ViewSet testleri
test_serializers.py   # Serializer testleri
test_services.py      # TMDB Service testleri
test_algorithms.py    # Öneri algoritması testleri
```

#### API Tests (Postman)
- Tüm endpoint'leri manual test
- Response format'larını doğrulama
- Performans testleri (load testing)
- Error handling testleri

#### User Acceptance Testing (UAT)
- 20+ kullanıcı ile beta test
- Kullanıcı feedback toplanması
- Önerilerin doğruluğu ölçümü
- UX/UI improvements

---

## 4. VERİTABANI MİMARİSİ

### Ana Tablolar

#### Users Tablosu
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password VARCHAR(128) NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    bio TEXT,
    profile_picture VARCHAR(500),
    date_of_birth DATE,
    total_movies_watched INT DEFAULT 0,
    avg_rating DECIMAL(3,1) DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE
);
```

#### Genres Tablosu
```sql
CREATE TABLE genres (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tmdb_id INT UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    name_tr VARCHAR(100)
);
```

#### Persons Tablosu
```sql
CREATE TABLE persons (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tmdb_id INT UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    profile_path VARCHAR(500),
    biography TEXT,
    birthday DATE,
    deathday DATE,
    place_of_birth VARCHAR(255),
    known_for_department VARCHAR(100),
    gender INT DEFAULT 0,
    popularity FLOAT DEFAULT 0.0,
    created_at DATETIME,
    updated_at DATETIME
);
```

#### Movies Tablosu
```sql
CREATE TABLE movies (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tmdb_id INT UNIQUE NOT NULL,
    imdb_id VARCHAR(20),
    title VARCHAR(255) NOT NULL,
    original_title VARCHAR(255),
    overview TEXT,
    tagline VARCHAR(500),
    poster_path VARCHAR(500),
    backdrop_path VARCHAR(500),
    release_date DATE,
    runtime INT,
    vote_average FLOAT DEFAULT 0.0,
    vote_count INT DEFAULT 0,
    popularity FLOAT DEFAULT 0.0,
    original_language VARCHAR(10),
    status VARCHAR(20),
    adult BOOLEAN DEFAULT FALSE,
    budget BIGINT DEFAULT 0,
    revenue BIGINT DEFAULT 0,
    homepage VARCHAR(500),
    created_at DATETIME,
    updated_at DATETIME,
    INDEX (tmdb_id),
    INDEX (title),
    INDEX (release_date),
    INDEX (vote_average)
);
```

#### Movies_Genres (M2M)
```sql
CREATE TABLE movies_genres (
    id INT PRIMARY KEY AUTO_INCREMENT,
    movie_id INT NOT NULL,
    genre_id INT NOT NULL,
    FOREIGN KEY (movie_id) REFERENCES movies(id),
    FOREIGN KEY (genre_id) REFERENCES genres(id),
    UNIQUE KEY unique_movie_genre (movie_id, genre_id)
);
```

#### MovieCast Tablosu
```sql
CREATE TABLE movie_cast (
    id INT PRIMARY KEY AUTO_INCREMENT,
    movie_id INT NOT NULL,
    person_id INT NOT NULL,
    character_name VARCHAR(255),
    cast_order INT,
    created_at DATETIME,
    FOREIGN KEY (movie_id) REFERENCES movies(id),
    FOREIGN KEY (person_id) REFERENCES persons(id),
    INDEX (movie_id),
    INDEX (person_id)
);
```

#### MovieCrew Tablosu
```sql
CREATE TABLE movie_crew (
    id INT PRIMARY KEY AUTO_INCREMENT,
    movie_id INT NOT NULL,
    person_id INT NOT NULL,
    department VARCHAR(100),
    job VARCHAR(100),
    created_at DATETIME,
    FOREIGN KEY (movie_id) REFERENCES movies(id),
    FOREIGN KEY (person_id) REFERENCES persons(id),
    INDEX (movie_id),
    INDEX (person_id)
);
```

### Planlanmış Tablolar

#### Ratings Tablosu (Kullanıcı Puanları)
```sql
CREATE TABLE ratings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    movie_id INT NOT NULL,
    score INT CHECK (score >= 1 AND score <= 10),
    review TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (movie_id) REFERENCES movies(id),
    UNIQUE KEY unique_user_movie (user_id, movie_id),
    INDEX (user_id),
    INDEX (movie_id)
);
```

#### Friendships Tablosu
```sql
CREATE TABLE friendships (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    friend_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, accepted, blocked
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (friend_id) REFERENCES users(id),
    UNIQUE KEY unique_friendship (user_id, friend_id),
    INDEX (user_id),
    INDEX (friend_id)
);
```

#### Compatibility_Scores Tablosu
```sql
CREATE TABLE compatibility_scores (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_1_id INT NOT NULL,
    user_2_id INT NOT NULL,
    score INT CHECK (score >= 0 AND score <= 100),
    common_movies INT,
    similar_genres JSON,
    similar_actors JSON,
    similar_directors JSON,
    calculated_at DATETIME,
    FOREIGN KEY (user_1_id) REFERENCES users(id),
    FOREIGN KEY (user_2_id) REFERENCES users(id),
    UNIQUE KEY unique_compatibility (user_1_id, user_2_id)
);
```

---

## 5. API ENDPOINTS

### Film Endpoints

```http
GET /api/movies/
GET /api/movies/{id}/
GET /api/movies/search/
GET /api/movies/popular/
GET /api/movies/trending/
GET /api/movies/upcoming/
GET /api/movies/top_rated/
GET /api/movies/{id}/similar/
GET /api/movies/by_genre/?genre_id=28
```

### Tür Endpoints

```http
GET /api/genres/
GET /api/genres/{id}/
```

### Kişi Endpoints

```http
GET /api/persons/
GET /api/persons/{id}/
```

---

## 6. PROJE DURUM RAPORU

### ✅ Tamamlanan (% 85)

**Altyapı:**
- [x] Django 5.0 + DRF Kurulumu
- [x] PostgreSQL/SQLite Veritabanı
- [x] Movie, Genre, Person, MovieCast, MovieCrew Modelleri
- [x] API ViewSets (Read-Only)
- [x] TMDB API Entegrasyonu (+ Dil Fallback)
- [x] Management Commands (sync_genres, sync_popular_movies, sync_all_movies, fix_movie_translations)
- [x] Film Listesi ve Detay API'ları
- [x] Arama, Filtreleme, Sıralama Özellikleri
- [x] Swagger/ReDoc Dokümantasyonu

**Kullanıcı Sistemi:**
- [x] User Registration/Login (Frontend)
- [x] User Profile (düzenleme, profil fotoğrafı)
- [x] Rating System (film puanlama)
- [x] Watchlist System (izleme listesi)
- [x] Friendship System (arkadaş ekle/kabul/reddet)

**Frontend:**
- [x] Django Templates MVP
- [x] Tailwind CSS ile modern tasarım
- [x] Ana sayfa (öneriler, trendler, yakında)
- [x] Film detay sayfası
- [x] Keşfet sayfası (Live Search + TMDB Hybrid)
- [x] Profil sayfası
- [x] Arkadaşlar sayfası
- [x] İzleme listesi sayfası
- [x] Dark/Light Mode
- [x] Türkçe/İngilizce dil desteği
- [x] Toast Notification sistemi

### 🔄 Devam Eden (% 10)

- [ ] Kullanıcı Onboarding (kayıt sonrası film seçimi)
- [ ] Kullanıcı Tarz Profili oluşturma ve kaydetme
- [ ] Hızlı Öneri Sistemi (tek kişilik mod - sorulu)
- [ ] Compatibility Score Algoritması (iki kişi uyumluluk)
- [ ] Quick Match (iki kişilik mod)

### ❌ Eksik (% 5)

- [ ] Notification System (Celery + E-mail)
- [ ] Grup Film Önerisi (3-4 kişi)
- [ ] JustWatch API (platform bilgisi)
- [ ] Unit & Integration Tests
- [ ] Production Deploy (Docker, CI/CD)

---

## 7. ZAMAN ÇİZELGESİ (Güncellenmiş)

| Hafta | İşlem | Durum |
|-------|-------|-------|
| 1-2 | Database & Models | ✅ Tamamlandı |
| 3-4 | API Endpoints | ✅ Tamamlandı |
| 5-6 | User System (Register, Login, Profile) | ✅ Tamamlandı |
| 7-8 | Rating & Watchlist System | ✅ Tamamlandı |
| 9-10 | Friendship System | ✅ Tamamlandı |
| 11-12 | Frontend MVP (Django Templates) | ✅ Tamamlandı |
| 13 | Kullanıcı Onboarding & Tarz Profili | 🔄 Sonraki |
| 14 | Hızlı Öneri Sistemi (Tek Kişi) | ⏳ Planlandı |
| 15 | Uyumluluk Algoritması & Quick Match | ⏳ Planlandı |
| 16 | Testing + Bug Fix + Deploy | ⏳ Planlandı |

---

## 8. TEKNOLOJI YIĞINI (Tech Stack)

### Backend
- **Django 5.0** - Web Framework
- **Django REST Framework** - API Development
- **Celery** - Task Queue
- **Redis** - Cache & Message Broker
- **PostgreSQL/SQLite** - Database

### Frontend
- **Django Templates** (MVP)
- **React.js** (İleri Aşama)
- **Tailwind CSS** - Styling
- **Fetch API / Axios** - HTTP Client

### Harici Servisler
- **TMDB API** - Film Verileri
- **SendGrid/AWS SES** - E-mail
- **JustWatch API** - Platform Bilgisi (Planlanmış)

### Deployment
- **Docker** - Containerization
- **Heroku/AWS/DigitalOcean** - Hosting
- **GitHub Actions** - CI/CD

---

## 9. KAYNAKLAR

- [TMDB API Dokümantasyonu](https://developer.themoviedb.org/docs)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery Dokümantasyonu](https://docs.celeryproject.io/)
- [PostgreSQL Dokümantasyonu](https://www.postgresql.org/docs/)

---

**Son Güncelleme:** 29 Aralık 2025
**Proje Durumu:** % 85 Tamamlanmış
**Sonraki Hedef:** Kullanıcı Onboarding & Tarz Profili Sistemi
