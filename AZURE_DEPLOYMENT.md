# 🚀 Azure Deployment Rehberi - MatchFlix

Bu rehber, MatchFlix projesini Azure'da canlıya almak için adım adım talimatlar içerir.

## 📋 Ön Hazırlık

### 1. Gerekli Hesaplar
- ✅ Azure for Students ($100 kredi)
- ✅ GitHub hesabı
- ✅ TMDB API Key

### 2. Büyük Dosyaları GitHub'a PUSHLAMADAN ÖNCE!

**ÖNEMLİ:** Bu dosyalar çok büyük, Azure Blob Storage'a yüklenecek:

```bash
# .gitignore'da olduğundan emin ol:
ml-25m/
ml-25m.zip
ncf_model.pkl
ncf_model_mappings.pkl
ncf_model_ml_mapping.pkl
db.sqlite3
```

---

## 🎯 ADIM 1: Azure Resources Oluşturma

### 1.1. Resource Group Oluştur

Azure Portal → Resource Groups → Create

```
Name: matchflix-rg
Region: West Europe
```

### 1.2. PostgreSQL Flexible Server Oluştur

Azure Portal → Create a resource → Azure Database for PostgreSQL

**Server Details:**
```
Resource group: matchflix-rg
Server name: matchflix-postgres
Region: West Europe
Version: 15
Compute + Storage: Burstable (B1ms) - 1 vCore, 2GB RAM (~$15/ay)
Administrator username: matchflix_admin
Password: [Güçlü bir şifre]
```

**Networking:**
```
☑️ Allow public access
☑️ Allow access from Azure services
```

**Firewall Rules:**
```
Add current client IP address (local testler için)
```

**Database Oluştur:**
Server oluştuktan sonra → Databases → Create
```
Database name: matchflix_db
```

### 1.3. Storage Account Oluştur (ML Model için)

Azure Portal → Create a resource → Storage account

```
Resource group: matchflix-rg
Storage account name: matchflixstorage (unique olmalı)
Region: West Europe
Performance: Standard
Redundancy: LRS (en ucuz)
```

**Container Oluştur:**
Storage → Containers → + Container
```
Name: matchflix
Public access level: Private
```

### 1.4. Azure Container Registry (Opsiyonel)

Eğer Docker image'ı private tutmak istersen:

```
Resource group: matchflix-rg
Registry name: matchflixregistry
SKU: Basic
```

---

## 🗄️ ADIM 2: ML Modelini Azure Blob'a Yükle

### 2.1. Azure Storage Explorer Kullan

1. [Azure Storage Explorer](https://azure.microsoft.com/en-us/products/storage/storage-explorer/) indir
2. Azure hesabınla giriş yap
3. Storage account → matchflixstorage → matchflix container

### 2.2. Modelleri Yükle

Local'den şu dosyaları yükle:
```
ncf_model.pkl → models/ncf_model.pkl
ncf_model_mappings.pkl → models/ncf_model_mappings.pkl
ncf_model_ml_mapping.pkl → models/ncf_model_ml_mapping.pkl
```

**Veya Azure CLI ile:**
```bash
# Azure CLI yükle: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli
az login

# Upload
az storage blob upload \
  --account-name matchflixstorage \
  --container-name matchflix \
  --name models/ncf_model.pkl \
  --file ncf_model.pkl \
  --auth-mode login

az storage blob upload \
  --account-name matchflixstorage \
  --container-name matchflix \
  --name models/ncf_model_mappings.pkl \
  --file ncf_model_mappings.pkl \
  --auth-mode login

az storage blob upload \
  --account-name matchflixstorage \
  --container-name matchflix \
  --name models/ncf_model_ml_mapping.pkl \
  --file ncf_model_ml_mapping.pkl \
  --auth-mode login
```

### 2.3. Connection String Al

Storage account → Access keys → key1 → Connection string (KOPYALA)

---

## 🌐 ADIM 3: Azure Web App for Containers Oluştur

### 3.1. Web App Oluştur

Azure Portal → Create a resource → Web App

```
Resource group: matchflix-rg
Name: matchflix-app (unique olmalı)
Publish: Container
Region: West Europe
Pricing Plan: Basic B1 (1.75GB RAM, ~$13/ay)
```

**Container Settings (Deployment Method seç):**

**Seçenek A - Docker Hub (Public):**
```
Image Source: Docker Hub
Image and tag: matchflix:latest (GitHub Actions ile push edilecek)
```

**Seçenek B - Azure Container Registry:**
```
Image Source: Azure Container Registry
Registry: matchflixregistry
Image: matchflix
Tag: latest
```

### 3.2. Application Settings (Environment Variables)

Web App → Configuration → Application settings

`.env.production.example` dosyasındaki tüm değişkenleri ekle:

```
SECRET_KEY=...
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production
ALLOWED_HOSTS=matchflix-app.azurewebsites.net
DB_NAME=matchflix_db
DB_USER=matchflix_admin
DB_PASSWORD=...
DB_HOST=matchflix-postgres.postgres.database.azure.com
DB_PORT=5432
TMDB_API_KEY=...
AZURE_STORAGE_CONNECTION_STRING=...
AZURE_CONTAINER_NAME=matchflix
SITE_URL=https://matchflix-app.azurewebsites.net
```

**WEBSITES_PORT ekle (önemli!):**
```
WEBSITES_PORT=8000
```

### 3.3. Startup Command

Web App → Configuration → General settings → Startup Command:

```bash
python manage.py migrate && python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:8000 --workers 2 --threads 4 config.wsgi:application
```

---

## 🐳 ADIM 4: Docker Image Build ve Push

### 4.1. Local'de Build Et

```bash
cd c:\Users\Mücahit\Desktop\MatchFlix

# Build
docker build -t matchflix:latest .

# Test (opsiyonel)
docker run -p 8000:8000 matchflix:latest
```

### 4.2. Docker Hub'a Push (Public)

```bash
# Docker Hub login
docker login

# Tag
docker tag matchflix:latest yourusername/matchflix:latest

# Push
docker push yourusername/matchflix:latest
```

### 4.3. Azure Container Registry'ye Push (Private)

```bash
# ACR login
az acr login --name matchflixregistry

# Tag
docker tag matchflix:latest matchflixregistry.azurecr.io/matchflix:latest

# Push
docker push matchflixregistry.azurecr.io/matchflix:latest
```

---

## 🔧 ADIM 5: Database Migration

### 5.1. SSH ile Bağlan

Web App → Development Tools → SSH → Go

**Veya Local'den:**
```bash
az webapp ssh --resource-group matchflix-rg --name matchflix-app
```

### 5.2. Migration Çalıştır

```bash
# SSH içinde:
cd /app
python manage.py migrate
python manage.py createsuperuser
```

---

## 🎨 ADIM 6: Static Files

WhiteNoise zaten aktif, ama kontrol için:

```bash
python manage.py collectstatic --noinput
```

---

## 📊 ADIM 7: ML Model İndir (İlk Çalıştırma)

Model'i Azure Blob'dan indirip kullanmak için `apps/recommendations/services.py` içinde şu kodu ekle:

```python
import os
from azure.storage.blob import BlobServiceClient
from django.conf import settings

def download_ml_models():
    """Azure Blob'dan ML modellerini indir"""
    if not settings.AZURE_STORAGE_CONNECTION_STRING:
        print("Azure Storage not configured, using local models")
        return
    
    blob_service = BlobServiceClient.from_connection_string(
        settings.AZURE_STORAGE_CONNECTION_STRING
    )
    container = blob_service.get_container_client(settings.AZURE_CONTAINER_NAME)
    
    models = [
        ('models/ncf_model.pkl', 'ncf_model.pkl'),
        ('models/ncf_model_mappings.pkl', 'ncf_model_mappings.pkl'),
        ('models/ncf_model_ml_mapping.pkl', 'ncf_model_ml_mapping.pkl'),
    ]
    
    for blob_path, local_path in models:
        local_file = os.path.join(settings.BASE_DIR, local_path)
        if not os.path.exists(local_file):
            print(f"Downloading {blob_path}...")
            blob_client = container.get_blob_client(blob_path)
            with open(local_file, 'wb') as f:
                f.write(blob_client.download_blob().readall())
            print(f"Downloaded {local_path}")
```

Bu fonksiyonu `wsgi.py` veya `__init__.py` içinde çağır (ilk başlatmada).

---

## 🔐 ADIM 8: Domain ve SSL

### 8.1. Custom Domain (Kendi Domain'in)

Web App → Custom domains → Add custom domain

```
Domain: matchflix.com
CNAME: matchflix-app.azurewebsites.net
```

### 8.2. SSL Certificate

Web App → TLS/SSL settings → Private Key Certificates → + Create App Service Managed Certificate

**Veya Let's Encrypt (ücretsiz):**
- [Let's Encrypt extension](https://github.com/shibayan/keyvault-acmebot) kullan

---

## 🚀 ADIM 9: GitHub Actions CI/CD (Opsiyonel)

`.github/workflows/azure-deploy.yml` oluştur:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: yourusername/matchflix:latest
      
      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Restart Web App
        run: |
          az webapp restart --resource-group matchflix-rg --name matchflix-app
```

**GitHub Secrets ekle:**
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`
- `AZURE_CREDENTIALS` (Service Principal credentials)

---

## 📈 ADIM 10: Monitoring ve Logs

### 10.1. Logs İzle

```bash
az webapp log tail --resource-group matchflix-rg --name matchflix-app
```

**Veya Azure Portal:**
Web App → Monitoring → Log stream

### 10.2. Application Insights (Opsiyonel)

Web App → Monitoring → Application Insights → Turn on

---

## ✅ Test Checklist

- [ ] PostgreSQL bağlantısı çalışıyor
- [ ] ML model Azure Blob'dan indirildi
- [ ] Static files yükleniyor
- [ ] `/health/` endpoint OK döndürüyor
- [ ] Admin panel açılıyor
- [ ] TMDB API çalışıyor
- [ ] Kullanıcı kaydı aktif
- [ ] Öneriler çalışıyor

---

## 💰 Tahmini Aylık Maliyet

| Servis | Plan | Aylık |
|--------|------|-------|
| Web App | B1 (1.75GB) | ~$13 |
| PostgreSQL | B1ms (2GB) | ~$15 |
| Storage | Standard LRS | ~$0.50 |
| **TOPLAM** | | **~$28.50** |

**$100 kredi ile:** ~3.5 ay

**Optimizasyon:**
- Web App → B1 yerine Free tier (ama sınırlı)
- PostgreSQL → Flexible Server Free tier (750 saat/ay)
- Her gün durdurup açarak krediyi uzat

---

## 🆘 Sorun Giderme

### Container başlamıyor
```bash
# Logs kontrol et
az webapp log tail --resource-group matchflix-rg --name matchflix-app

# Restart
az webapp restart --resource-group matchflix-rg --name matchflix-app
```

### Database connection error
- Firewall rules kontrol et
- Connection string doğru mu?
- PostgreSQL running durumda mı?

### ML model yüklenmiyor
- Azure Storage connection string doğru mu?
- Blob path'ler doğru mu?
- Container public mi private mı?

---

## 📞 İletişim

Sorun olursa:
1. Azure Portal → Logs
2. Health check: `https://matchflix-app.azurewebsites.net/health/`
3. Admin: `https://matchflix-app.azurewebsites.net/admin/`

Başarılar! 🎉
