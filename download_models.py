"""
Azure Blob Storage - ML Model Downloader
=========================================
Azure Blob Storage'dan ML modellerini indirir.
Production ortamında otomatik çalışır.
"""

import os
import sys
from pathlib import Path
from django.conf import settings


def download_ml_models():
    """Azure Blob Storage'dan ML modellerini indir"""
    
    # Azure Storage yapılandırılmamışsa atla
    if not hasattr(settings, 'AZURE_STORAGE_CONNECTION_STRING') or not settings.AZURE_STORAGE_CONNECTION_STRING:
        print("ℹ️  Azure Storage not configured. Using local models if available.")
        return False
    
    try:
        from azure.storage.blob import BlobServiceClient
        
        print("📦 Connecting to Azure Blob Storage...")
        blob_service = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )
        container_client = blob_service.get_container_client(settings.AZURE_CONTAINER_NAME)
        
        # İndirilecek modeller
        models_to_download = [
            {
                'blob_path': settings.ML_MODEL_AZURE_PATH,
                'local_path': settings.BASE_DIR / 'ncf_model.pkl',
                'name': 'NCF Model'
            },
            {
                'blob_path': settings.ML_MODEL_MAPPINGS_AZURE_PATH,
                'local_path': settings.BASE_DIR / 'ncf_model_mappings.pkl',
                'name': 'NCF Model Mappings'
            },
            {
                'blob_path': settings.ML_MODEL_ML_MAPPING_AZURE_PATH,
                'local_path': settings.BASE_DIR / 'ncf_model_ml_mapping.pkl',
                'name': 'NCF ML Mapping'
            },
        ]
        
        downloaded_count = 0
        skipped_count = 0
        
        for model_info in models_to_download:
            local_file = model_info['local_path']
            
            # Zaten varsa atla
            if local_file.exists():
                file_size_mb = local_file.stat().st_size / (1024 * 1024)
                print(f"✅ {model_info['name']} already exists ({file_size_mb:.1f} MB)")
                skipped_count += 1
                continue
            
            # İndir
            print(f"⬇️  Downloading {model_info['name']} from {model_info['blob_path']}...")
            try:
                blob_client = container_client.get_blob_client(model_info['blob_path'])
                
                # İndirmeyi başlat
                with open(local_file, 'wb') as f:
                    download_stream = blob_client.download_blob()
                    f.write(download_stream.readall())
                
                file_size_mb = local_file.stat().st_size / (1024 * 1024)
                print(f"✅ {model_info['name']} downloaded successfully ({file_size_mb:.1f} MB)")
                downloaded_count += 1
                
            except Exception as e:
                print(f"❌ Failed to download {model_info['name']}: {e}")
                # Partial dosyayı sil
                if local_file.exists():
                    local_file.unlink()
        
        print(f"\n📊 Download Summary:")
        print(f"   Downloaded: {downloaded_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Total: {len(models_to_download)}")
        
        return downloaded_count > 0
        
    except ImportError:
        print("❌ azure-storage-blob not installed. Install it with: pip install azure-storage-blob")
        return False
    except Exception as e:
        print(f"❌ Error downloading models from Azure: {e}")
        return False


def check_local_models():
    """Local'de modellerin varlığını kontrol et"""
    
    model_files = [
        'ncf_model.pkl',
        'ncf_model_mappings.pkl',
        'ncf_model_ml_mapping.pkl',
    ]
    
    print("\n🔍 Checking local ML models...")
    all_exist = True
    
    for model_file in model_files:
        model_path = settings.BASE_DIR / model_file
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ {model_file} ({size_mb:.1f} MB)")
        else:
            print(f"   ❌ {model_file} NOT FOUND")
            all_exist = False
    
    return all_exist


if __name__ == '__main__':
    # Django setup
    sys.path.insert(0, str(Path(__file__).parent))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    
    import django
    django.setup()
    
    # Önce local'de var mı kontrol et
    if check_local_models():
        print("\n✅ All models are available locally. No download needed.")
    else:
        print("\n📥 Some models are missing. Attempting download from Azure...")
        download_ml_models()
        
        # Tekrar kontrol
        if check_local_models():
            print("\n🎉 All models are ready!")
        else:
            print("\n⚠️  Some models are still missing. Please check Azure Blob Storage.")
