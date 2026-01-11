# MatchFlix - Azure App Service (Docker'sız) Deployment Rehberi

Bu rehber, MatchFlix'i Docker kullanmadan Azure App Service'e deploy etmek için adım adım talimatlar içerir.

---

## 📋 Gereksinimler

- ✅ Azure for Students hesabı ($100 kredi)
- ✅ Azure CLI yüklü (`winget install Microsoft.AzureCLI`)
- ✅ Git yüklü
- ✅ TMDB API Key

---

## 🚀 Hızlı Deployment (5 Adım)

### Adım 1: Azure CLI'ye Giriş Yap

```powershell
az login
```

Tarayıcı açılacak, Azure hesabınla giriş yap.

---

### Adım 2: Resource Group Oluştur

```powershell
az group create --name matchflix-rg --location westeurope
```

---

### Adım 3: App Service Plan Oluştur

```powershell
# Free tier (test için)
az appservice plan create --name matchflix-plan --resource-group matchflix-rg --sku F1 --is-linux

# VEYA B1 tier (production için - $13/ay)
az appservice plan create --name matchflix-plan --resource-group matchflix-rg --sku B1 --is-linux
```

---

### Adım 4: Web App Oluştur ve Deploy Et

```powershell
# Web App oluştur (Python 3.11)
az webapp create --resource-group matchflix-rg --plan matchflix-plan --name matchflix-app --runtime "PYTHON:3.11"

# GitHub'dan deploy (SCM)
az webapp deployment source config --name matchflix-app --resource-group matchflix-rg --repo-url https://github.com/KULLANICI_ADIN/matchflix --branch master --manual-integration

# VEYA Local'den deploy (ZIP)
cd C:\Users\Mücahit\Desktop\MatchFlix

# Önce requirements.txt'i güncelle (gerekirse)
pip freeze > requirements.txt

# Deploy et
az webapp up --name matchflix-app --resource-group matchflix-rg --runtime "PYTHON:3.11" --sku B1
```

---

### Adım 5: Environment Variables Ayarla

```powershell
# Tek tek ayarla
az webapp config appsettings set --name matchflix-app --resource-group matchflix-rg --settings SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"

az webapp config appsettings set --name matchflix-app --resource-group matchflix-rg --settings DEBUG="False"

az webapp config appsettings set --name matchflix-app --resource-group matchflix-rg --settings DJANGO_SETTINGS_MODULE="config.settings.production"

az webapp config appsettings set --name matchflix-app --resource-group matchflix-rg --settings ALLOWED_HOSTS="matchflix-app.azurewebsites.net"

az webapp config appsettings set --name matchflix-app --resource-group matchflix-rg --settings TMDB_API_KEY="YOUR_TMDB_API_KEY"

az webapp config appsettings set --name matchflix-app --resource-group matchflix-rg --settings SITE_URL="https://matchflix-app.azurewebsites.net"

az webapp config appsettings set --name matchflix-app --resource-group matchflix-rg --settings SCM_DO_BUILD_DURING_DEPLOYMENT="true"
```

**VEYA hepsini bir kerede:**

```powershell
az webapp config appsettings set --name matchflix-app --resource-group matchflix-rg --settings `
  SECRET_KEY="your-secret-key-here" `
  DEBUG="False" `
  DJANGO_SETTINGS_MODULE="config.settings.production" `
  ALLOWED_HOSTS="matchflix-app.azurewebsites.net" `
  TMDB_API_KEY="your-tmdb-key" `
  SITE_URL="https://matchflix-app.azurewebsites.net" `
  SCM_DO_BUILD_DURING_DEPLOYMENT="true"
```

---

### Adım 6: Startup Command Ayarla

```powershell
az webapp config set --name matchflix-app --resource-group matchflix-rg --startup-file "startup.sh"
```

---

## 🗄️ PostgreSQL Database (Opsiyonel)

SQLite production için yeterli değilse PostgreSQL ekle:

```powershell
# PostgreSQL Flexible Server oluştur
az postgres flexible-server create `
  --resource-group matchflix-rg `
  --name matchflix-postgres `
  --location westeurope `
  --admin-user matchflix_admin `
  --admin-password "YOUR_SECURE_PASSWORD" `
  --sku-name Standard_B1ms `
  --tier Burstable `
  --storage-size 32 `
  --version 15

# Database oluştur
az postgres flexible-server db create `
  --resource-group matchflix-rg `
  --server-name matchflix-postgres `
  --database-name matchflix_db

# Firewall rule ekle (Azure services)
az postgres flexible-server firewall-rule create `
  --resource-group matchflix-rg `
  --name matchflix-postgres `
  --rule-name AllowAzure `
  --start-ip-address 0.0.0.0 `
  --end-ip-address 0.0.0.0

# Web App'e database connection ekle
az webapp config appsettings set --name matchflix-app --resource-group matchflix-rg --settings `
  DB_NAME="matchflix_db" `
  DB_USER="matchflix_admin" `
  DB_PASSWORD="YOUR_SECURE_PASSWORD" `
  DB_HOST="matchflix-postgres.postgres.database.azure.com" `
  DB_PORT="5432"
```

---

## 🔧 Deployment Sonrası

### Migration Çalıştır

```powershell
# SSH ile bağlan
az webapp ssh --resource-group matchflix-rg --name matchflix-app

# İçeride:
cd /home/site/wwwroot
source antenv/bin/activate
python manage.py migrate
python manage.py createsuperuser
```

### Logs İzle

```powershell
az webapp log tail --name matchflix-app --resource-group matchflix-rg
```

### Restart

```powershell
az webapp restart --name matchflix-app --resource-group matchflix-rg
```

---

## ✅ Deployment Checklist

- [ ] `az login` ile giriş yapıldı
- [ ] Resource group oluşturuldu
- [ ] App Service Plan oluşturuldu
- [ ] Web App oluşturuldu
- [ ] Environment variables ayarlandı
- [ ] Startup command ayarlandı
- [ ] Code deploy edildi
- [ ] Migration çalıştırıldı
- [ ] Admin user oluşturuldu
- [ ] Site test edildi

---

## 🌐 URL'ler

- **Production:** https://matchflix-app.azurewebsites.net
- **Admin Panel:** https://matchflix-app.azurewebsites.net/admin/
- **Health Check:** https://matchflix-app.azurewebsites.net/health/
- **Azure Portal:** https://portal.azure.com

---

## 💰 Maliyet

| Plan | RAM | CPU | Aylık |
|------|-----|-----|-------|
| F1 (Free) | 1GB | Shared | $0 |
| B1 (Basic) | 1.75GB | 1 Core | ~$13 |
| B2 (Basic) | 3.5GB | 2 Core | ~$26 |

**$100 Azure kredisi ile:** ~7 ay B1 tier kullanabilirsin!

---

## 🆘 Sorun Giderme

### "ModuleNotFoundError: No module named 'xxx'"
```powershell
# requirements.txt'e modülü ekle
# Tekrar deploy et
az webapp up --name matchflix-app
```

### "Application Error"
```powershell
# Logs'a bak
az webapp log tail --name matchflix-app --resource-group matchflix-rg

# Restart dene
az webapp restart --name matchflix-app --resource-group matchflix-rg
```

### Static files yüklenmiyor
```powershell
# SSH ile bağlan
az webapp ssh --name matchflix-app --resource-group matchflix-rg

# Collectstatic çalıştır
python manage.py collectstatic --noinput
```

---

## 🎉 Başarılı Deployment!

Site artık canlı:
```
https://matchflix-app.azurewebsites.net
```
