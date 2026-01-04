# 📚 MatchFlix - Azure Deployment Özet

## ✅ Tamamlanan Hazırlıklar

### 1. Docker Dosyaları
- ✅ `Dockerfile` - Multi-stage production build
- ✅ `.dockerignore` - Gereksiz dosyaları hariç tut
- ✅ `docker-compose.yml` - Local test için
- ✅ `nginx.conf` - Reverse proxy configuration

### 2. Production Ayarları
- ✅ `requirements.txt` - Gunicorn, WhiteNoise, Azure SDK eklendi
- ✅ `config/settings/production.py` - WhiteNoise, Azure Blob, Security headers
- ✅ `.env.production.example` - Production environment template
- ✅ Health check endpoint `/health/` eklendi

### 3. Dokümantasyon
- ✅ `AZURE_DEPLOYMENT.md` - Detaylı deployment rehberi
- ✅ `README.md` - Proje dokümantasyonu
- ✅ `download_models.py` - Azure Blob'dan ML model indirme scripti

---

## 🚀 Deployment Süreci (Özet)

### Adım 1: Azure Resources
```
1. Resource Group: matchflix-rg
2. PostgreSQL: matchflix-postgres (B1ms, 2GB RAM)
3. Storage Account: matchflixstorage
   → Container: matchflix
4. Web App: matchflix-app (B1, 1.75GB RAM)
```

### Adım 2: ML Modelleri Yükle
```bash
# Azure Storage Explorer veya Azure CLI ile:
ncf_model.pkl → models/ncf_model.pkl
ncf_model_mappings.pkl → models/ncf_model_mappings.pkl
ncf_model_ml_mapping.pkl → models/ncf_model_ml_mapping.pkl
```

### Adım 3: Docker Build & Push
```bash
# Build
docker build -t matchflix:latest .

# Push (Docker Hub)
docker tag matchflix:latest yourusername/matchflix:latest
docker push yourusername/matchflix:latest
```

### Adım 4: Web App Configuration
```
Application Settings:
- SECRET_KEY=...
- DEBUG=False
- DJANGO_SETTINGS_MODULE=config.settings.production
- DB_HOST=matchflix-postgres.postgres.database.azure.com
- DB_NAME=matchflix_db
- DB_USER=matchflix_admin
- DB_PASSWORD=***
- AZURE_STORAGE_CONNECTION_STRING=***
- TMDB_API_KEY=***
- WEBSITES_PORT=8000

Startup Command:
python manage.py migrate && python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:8000 --workers 2 config.wsgi:application
```

### Adım 5: Deploy & Test
```bash
# Web App restart
az webapp restart --resource-group matchflix-rg --name matchflix-app

# Test
curl https://matchflix-app.azurewebsites.net/health/
```

---

## 💰 Maliyet Tahmini

| Kaynak | Detay | Aylık Maliyet |
|--------|-------|---------------|
| **Web App** | B1 (1.75GB RAM, 1 vCore) | ~$13 |
| **PostgreSQL** | B1ms (2GB RAM, 1 vCore) | ~$15 |
| **Storage** | Standard LRS (10GB) | ~$0.50 |
| **Bandwidth** | 5GB outbound | Ücretsiz |
| **TOPLAM** | | **~$28.50/ay** |

**$100 kredi ile:** ~3.5 ay kullanım

---

## 🔧 Optimizasyon İpuçları

### Krediyi Uzatma
```bash
# Gece kapatıp sabah aç (geliştirme aşamasında)
az webapp stop --resource-group matchflix-rg --name matchflix-app
az webapp start --resource-group matchflix-rg --name matchflix-app
```

### Log Takibi
```bash
# Real-time logs
az webapp log tail --resource-group matchflix-rg --name matchflix-app

# Stream logs
az webapp log download --resource-group matchflix-rg --name matchflix-app
```

### Backup
```bash
# Database backup
az postgres flexible-server backup create \
  --resource-group matchflix-rg \
  --name matchflix-postgres \
  --backup-name daily-backup
```

---

## 🎯 Kontrol Listesi (Deploy Öncesi)

### GitHub
- [ ] Büyük dosyalar `.gitignore`'da (ml-25m/, *.pkl, db.sqlite3)
- [ ] Kod GitHub'a push edildi
- [ ] `.env` dosyası push edilmedi

### Azure
- [ ] Resource Group oluşturuldu
- [ ] PostgreSQL server oluşturuldu ve database eklendi
- [ ] Storage Account oluşturuldu
- [ ] ML modeller Blob Storage'a yüklendi
- [ ] Web App oluşturuldu
- [ ] Application Settings eklendi

### Docker
- [ ] Dockerfile test edildi (local build)
- [ ] Image Docker Hub/ACR'a push edildi

### Database
- [ ] PostgreSQL firewall rules ayarlandı
- [ ] Migration çalıştırıldı
- [ ] Superuser oluşturuldu

### Domain (Opsiyonel)
- [ ] Custom domain eklendi
- [ ] SSL certificate ayarlandı

---

## 🆘 Sık Karşılaşılan Sorunlar

### "Application Error" sayfası
**Çözüm:**
```bash
# Logs kontrol et
az webapp log tail --resource-group matchflix-rg --name matchflix-app

# Restart
az webapp restart --resource-group matchflix-rg --name matchflix-app
```

### Database bağlantı hatası
**Kontroller:**
- PostgreSQL running durumda mı?
- Firewall'da Azure services allowed mı?
- DB_HOST, DB_USER, DB_PASSWORD doğru mu?

### ML model yüklenmiyor
**Kontroller:**
- Azure Storage connection string doğru mu?
- Blob path'ler doğru mu? (`models/ncf_model.pkl`)
- Container "matchflix" adında mı?

### Static files yüklenmiyor
**Çözüm:**
```bash
# SSH içinde
python manage.py collectstatic --noinput

# WhiteNoise debug
DEBUG=True --> Hatayı göster
```

---

## 📞 Yardım ve Destek

### Faydalı Komutlar
```bash
# Web App bilgileri
az webapp show --resource-group matchflix-rg --name matchflix-app

# PostgreSQL bilgileri
az postgres flexible-server show --resource-group matchflix-rg --name matchflix-postgres

# Storage bilgileri
az storage account show --name matchflixstorage

# Tüm kaynakları listele
az resource list --resource-group matchflix-rg --output table
```

### Dokümantasyon Linkleri
- [Azure Web App for Containers](https://learn.microsoft.com/en-us/azure/app-service/quickstart-custom-container)
- [Azure PostgreSQL](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/)
- [Azure Blob Storage](https://learn.microsoft.com/en-us/azure/storage/blobs/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)

---

## 🎉 Deployment Sonrası

### Test Endpoints
```
Health: https://matchflix-app.azurewebsites.net/health/
Home: https://matchflix-app.azurewebsites.net/
Admin: https://matchflix-app.azurewebsites.net/admin/
API Docs: https://matchflix-app.azurewebsites.net/api/schema/swagger/
```

### Monitoring
Azure Portal → Web App → Monitoring → Application Insights

### Scaling (İhtiyaç Durumunda)
```bash
# Scale up (daha güçlü makine)
az appservice plan update --resource-group matchflix-rg --name <plan-name> --sku B2

# Scale out (daha fazla instance)
az webapp scale --resource-group matchflix-rg --name matchflix-app --instance-count 2
```

---

**Son Güncelleme:** 2026-01-04
**Versiyon:** 1.0
**Hazırlayan:** Antigravity AI Assistant
