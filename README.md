# 🎬 MatchFlix

AI destekli film öneri ve sosyal platform

## 🚀 Hızlı Başlangıç

### Local Development

1. **Clone & Install**
```bash
git clone https://github.com/youruser name/matchflix.git
cd matchflix
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment Variables**
```bash
cp .env.example .env
# .env dosyasını düzenle
```

3. **Database**
```bash
python manage.py migrate
python manage.py createsuperuser
```

4. **Run**
```bash
python manage.py runserver
```

### Docker Development

```bash
# Build & Run
docker-compose up --build

# Migrate
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

## 🌐 Azure Deployment

Detaylıanaliz için: [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)

**Kısa Özet:**
1. Azure for Students hesabı aç ($100 kredi)
2. PostgreSQL Flexible Server oluştur
3. Storage Account oluştur, ML modellerini yükle
4. Web App for Containers oluştur
5. Docker image build & push
6. Environment variables ayarla
7. Deploy!

## 📦 Özellikler

- 🤖 **AI Öneri Sistemi** - PyTorch NCF model
- 🎭 **Film Keşfi** - TMDB API entegrasyonu
- 👥 **Sosyal Özellikler** - Arkadaş ekleme, ortak beğeniler
- 📊 **Detaylı İstatistikler** - İzleme geçmişi, tür analizi
- 🔍 **Akıllı Arama** - Fuzzy search, live TMDB arama
- ⚡ **Quick Match** - Hızlı öneri, arkadaşla eşleşme

## 🛠 Teknoloji Stack

- **Backend:** Django 5.0, DRF
- **Database:** PostgreSQL / SQLite
- **Cache:** Redis / LocMemCache
- **ML:** PyTorch, scikit-learn
- **API:** TMDB API
- **Deployment:** Docker, Azure

## 📁 Proje Yapısı

```
matchflix/
├── apps/
│   ├── movies/          # Film modelleri ve servisleri
│   ├── users/           # Kullanıcı yönetimi
│   ├── recommendations/ # AI öneri sistemi
│   └── notifications/   # Bildirimler
├── config/              # Django settings
├── templates/           # HTML templates
├── static/              # CSS, JS, images
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 🔧 Environment Variables

Gerekli değişkenler:

```env
SECRET_KEY=your-secret-key
DEBUG=True
TMDB_API_KEY=your-tmdb-key
DB_NAME=matchflix_db
DB_USER=matchflix_user
DB_PASSWORD=your-password
```

Tam liste: `.env.example` veya `.env.production.example`

## 🧪 Testing

```bash
pytest
```

## 📝 License

MIT

## 👨‍💻 Developer

Mücahit Akca - Bitirme Projesi
