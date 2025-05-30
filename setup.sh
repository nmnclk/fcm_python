#!/bin/bash

# FCM Python Uygulaması Otomatik Kurulum Script'i
# Bu script virtual environment kurar ve gerekli paketleri yükler

set -e  # Hata durumunda script'i durdur

echo "🔥 FCM Python Uygulaması Kurulum Script'i"
echo "=========================================="

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Python versiyonunu kontrol et
echo -e "${BLUE}🐍 Python versiyonu kontrol ediliyor...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 bulunamadı! Lütfen Python 3.7+ yükleyin.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
echo -e "${GREEN}✅ Python ${PYTHON_VERSION} bulundu${NC}"

# pip kontrolü
echo -e "${BLUE}📦 pip kontrol ediliyor...${NC}"
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 bulunamadı! pip yüklenecek...${NC}"
    python3 -m ensurepip --upgrade
fi
echo -e "${GREEN}✅ pip hazır${NC}"

# Virtual environment oluştur
VENV_DIR="venv"
echo -e "${BLUE}🏗️  Virtual environment oluşturuluyor...${NC}"

if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment zaten mevcut, yeniden oluşturuluyor...${NC}"
    rm -rf "$VENV_DIR"
fi

python3 -m venv "$VENV_DIR"
echo -e "${GREEN}✅ Virtual environment oluşturuldu: ${VENV_DIR}${NC}"

# Virtual environment'ı aktifleştir
echo -e "${BLUE}🔌 Virtual environment aktifleştiriliyor...${NC}"
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✅ Virtual environment aktif${NC}"

# pip'i güncelle
echo -e "${BLUE}⬆️  pip güncelleniyor...${NC}"
pip install --upgrade pip
echo -e "${GREEN}✅ pip güncellendi${NC}"

# requirements.txt dosyası oluştur
echo -e "${BLUE}📋 requirements.txt oluşturuluyor...${NC}"
cat > requirements.txt << EOF
# Firebase Admin SDK
firebase-admin>=6.2.0

# JSON işlemleri ve dosya yönetimi (Python built-in)
# pathlib (Python 3.4+)
# json (Python built-in)
# os (Python built-in)
# sys (Python built-in)

# Typing desteği (Python 3.5+)
# typing (Python 3.5+)
EOF

echo -e "${GREEN}✅ requirements.txt oluşturuldu${NC}"

# Gerekli paketleri yükle
echo -e "${BLUE}📦 Gerekli paketler yükleniyor...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✅ Tüm paketler başarıyla yüklendi${NC}"

# Gerekli klasörleri oluştur
echo -e "${BLUE}📁 Gerekli klasörler oluşturuluyor...${NC}"
mkdir -p firebase_keys
echo -e "${GREEN}✅ firebase_keys klasörü oluşturuldu${NC}"

# Başlangıç script'i oluştur
echo -e "${BLUE}🚀 Başlangıç script'i oluşturuluyor...${NC}"
cat > run.sh << 'EOF'
#!/bin/bash

# FCM Python Uygulaması Başlatıcı

# Virtual environment'ı aktifleştir
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment aktifleştirildi"
else
    echo "❌ Virtual environment bulunamadı! setup.sh çalıştırın."
    exit 1
fi

# Uygulamayı başlat
echo "🔥 FCM Uygulaması başlatılıyor..."
python fcm_sender.py
EOF

chmod +x run.sh
echo -e "${GREEN}✅ run.sh oluşturuldu ve çalıştırılabilir yapıldı${NC}"

# .gitignore oluştur
echo -e "${BLUE}📝 .gitignore oluşturuluyor...${NC}"
cat > .gitignore << EOF
# Virtual Environment
venv/
env/

# Firebase Keys (güvenlik için)
firebase_keys/*.json

# Device tokens (gizlilik için)
device_tokens.json

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd

# IDE files
.vscode/
.idea/
*.swp
*.swo

# macOS files
.DS_Store

# Log files
*.log
EOF

echo -e "${GREEN}✅ .gitignore oluşturuldu${NC}"

# README.md güncelle/oluştur
echo -e "${BLUE}📖 README.md oluşturuluyor...${NC}"
cat > README.md << 'EOF'
# 🔥 FCM Python Bildirim Gönderici

Firebase Cloud Messaging (FCM) kullanarak kolayca push notification gönderebileceğiniz Python uygulaması.

## 🚀 Hızlı Başlangıç

### 1. Kurulum
```bash
# Otomatik kurulum
chmod +x setup.sh
./setup.sh
```

### 2. Firebase Ayarları
1. Firebase Console'dan service account key (JSON) dosyalarınızı indirin
2. JSON dosyalarını `firebase_keys/` klasörüne koyun
3. Dosya adları proje tanımlaması olarak kullanılacak

### 3. Uygulamayı Çalıştır
```bash
# Kolay başlatma
./run.sh

# Veya manuel
source venv/bin/activate
python fcm_sender.py
```

## 📱 Özellikler

- ✅ Çoklu Firebase projesi desteği
- ✅ Cihaz kategorileri (iPhone, Android, iPad, Web, Test)
- ✅ Toplu bildirim gönderme
- ✅ İnteraktif menü sistemi
- ✅ Token yönetimi
- ✅ Türkçe arayüz

## 📁 Dosya Yapısı

```
fcm_python/
├── fcm_sender.py           # Ana uygulama
├── setup.sh               # Kurulum script'i
├── run.sh                 # Başlatma script'i
├── requirements.txt       # Python bağımlılıkları
├── firebase_keys/         # Firebase JSON keys
├── device_tokens.json     # Cihaz token'ları
└── venv/                  # Virtual environment
```

## 🔧 Gereksinimler

- Python 3.7+
- firebase-admin
- Firebase service account key dosyaları

## 🛡️ Güvenlik

- Firebase key dosyaları git'e commit edilmez
- Token dosyaları gizlilik için ignore edilir
- Service account permissions minimum düzeyde tutulmalı

## 🆘 Sorun Giderme

1. **Firebase Auth Hatası**: Service account key dosyalarınızı kontrol edin
2. **Token Hatası**: Geçersiz token'ları temizleyin
3. **Python Hatası**: Python 3.7+ kullandığınızdan emin olun

EOF

echo -e "${GREEN}✅ README.md oluşturuldu${NC}"

# Başarı mesajı
echo ""
echo -e "${GREEN}🎉 KURULUM TAMAMLANDI!${NC}"
echo "=========================================="
echo -e "${BLUE}📋 Sonraki adımlar:${NC}"
echo -e "1. ${YELLOW}Firebase Console'dan service account key dosyalarını firebase_keys/ klasörüne ekleyin${NC}"
echo -e "2. ${YELLOW}./run.sh ile uygulamayı başlatın${NC}"
echo ""
echo -e "${BLUE}📁 Oluşturulan dosyalar:${NC}"
echo "  • venv/ (virtual environment)"
echo "  • requirements.txt (Python bağımlılıkları)"
echo "  • run.sh (başlatma script'i)"
echo "  • .gitignore (git ignore dosyası)"
echo "  • README.md (dokümantasyon)"
echo "  • firebase_keys/ (Firebase key klasörü)"
echo ""
echo -e "${GREEN}✨ Artık FCM uygulamanız kullanıma hazır!${NC}" 