# 🔥 FCM Python Bildirim Gönderici

İnteraktif Firebase Cloud Messaging (FCM) bildirim gönderme uygulaması. Birden çok Firebase projesi için bildirim gönderme, detaylı hata loglama ve proje-token yönetimi özelliklerine sahiptir.

## 🚀 Özellikler

### 📱 Gelişmiş Token Yönetimi
- **Proje-Token Birleşik Yapısı**: Token'lar artık projeler içinde organize edilir
- **Token Adlandırma**: Her token'a özel ad verilebilir (ör: "Ali'nin iPhone", "Test Cihazı")
- **Kategori Desteği**: iPhone, Android, iPad, Web, Test kategorileri
- **Otomatik Dönüştürme**: Eski token yapısı otomatik olarak yeni yapıya dönüştürülür

### 🗂️ Proje Yönetimi
- **Çoklu Proje Desteği**: Birden çok Firebase projesi yönetimi
- **Otomatik Proje Algılama**: firebase_keys/ klasöründeki JSON dosyaları otomatik taranır
- **Proje Durumu**: Hangi projelerin aktif olduğu görülebilir

### 📤 Gelişmiş Bildirim Gönderimi
- **Token Gönderimi**: Belirli cihazlara bildirim gönderme
- **Topic Gönderimi**: Topic'lere bildirim gönderme
- **Platform Özel Ayarlar**: Android ve iOS için özel konfigürasyonlar
- **Detaylı Yanıt Analizi**: Her token için başarı/hata analizi

### 📊 Detaylı Hata Yönetimi ve Loglama
- **Günlük Log Dosyaları**: Tarih bazlı log tutma
- **Hata Kategorileri**: Unregistered, SenderIdMismatch, QuotaExceeded
- **Başarısız Token Raporu**: Başarısız token'ların detaylı analizi
- **Kritik Hata Kayıtları**: Sistem seviyesi hataların kaydı

## 📜 Script Dosyaları

### 🛠️ setup.sh - Otomatik Kurulum Script'i

Projeyi sıfırdan kurmak ve çalıştırmaya hazır hale getirmek için kullanılan kapsamlı kurulum script'i.

#### Özellikler:
- **Python Kontrolü**: Python 3.7+ varlığını kontrol eder
- **Virtual Environment**: Otomatik venv oluşturur ve aktifleştirir
- **Paket Yönetimi**: requirements.txt oluşturur ve bağımlılıkları yükler
- **Klasör Yapısı**: Gerekli klasörleri (firebase_keys, logs) oluşturur
- **Git Yapılandırması**: .gitignore dosyası oluşturur
- **Script Hazırlığı**: run.sh dosyasını oluşturur ve çalıştırılabilir yapar
- **Dokümantasyon**: README.md dosyasını günceller

#### Kullanım:
```bash
chmod +x setup.sh && ./setup.sh
```

#### Oluşturulan Dosyalar:
- `venv/` - Virtual environment
- `requirements.txt` - Python bağımlılıkları
- `run.sh` - Başlatma script'i
- `.gitignore` - Git ignore kuralları
- `firebase_keys/` - Firebase key klasörü

### 🚀 run.sh - Hızlı Başlatma Script'i

Uygulamayı tek komutla başlatmak için kullanılan basit ve etkili script.

#### Özellikler:
- **Environment Kontrolü**: Virtual environment varlığını kontrol eder
- **Otomatik Aktifleştirme**: venv'i otomatik aktifleştirir
- **Hata Yönetimi**: Virtual environment yoksa uyarı verir
- **Temiz Çıktı**: Kullanıcı dostu bilgi mesajları

#### Kullanım:
```bash
chmod +x run.sh && ./run.sh
```

#### Çalışma Mantığı:
1. `venv/` klasörünün varlığını kontrol eder
2. Virtual environment'ı aktifleştirir
3. `fcm_sender.py` uygulamasını başlatır
4. Hata durumunda açıklayıcı mesaj verir

### 📋 Script Bağımlılıkları

Her iki script de birbirleriyle uyumlu çalışacak şekilde tasarlanmıştır:

1. **İlk Kurulum**: `setup.sh` çalıştırılır
2. **Günlük Kullanım**: `run.sh` ile uygulama başlatılır
3. **Güncelleme**: `setup.sh` tekrar çalıştırılabilir

## 📂 Dosya Yapısı

```
fcm_python/
├── fcm_sender.py              # Ana uygulama
├── setup.sh                   # 🛠️ Otomatik kurulum script'i
├── run.sh                     # 🚀 Hızlı başlatma script'i
├── requirements.txt           # Python bağımlılıkları
├── device_tokens.json         # Birleşik token ve proje yapısı
├── firebase_keys/             # Firebase JSON key dosyaları
│   ├── proje1-firebase.json
│   └── proje2-firebase.json
├── venv/                      # Virtual environment (setup.sh tarafından oluşturulur)
└── logs/                      # Log dosyaları
    ├── fcm_log_YYYYMMDD.log           # Genel loglar
    ├── failed_tokens_YYYYMMDD.json    # Başarısız token'lar
    ├── critical_errors_YYYYMMDD.json  # Kritik hatalar
    └── topic_errors_YYYYMMDD.json     # Topic hataları
```

## 🔧 Kurulum

### Otomatik Kurulum (Önerilen)
```bash
# Kurulum script'ini çalıştırılabilir yap
chmod +x setup.sh

# Otomatik kurulumu başlat
./setup.sh
```

### Manuel Kurulum
1. **Gereksinimler**
```bash
pip install firebase-admin
```

2. **Firebase Ayarları**
   - Firebase Console'dan service account JSON key dosyalarını indirin
   - JSON dosyalarını `firebase_keys/` klasörüne koyun

3. **Çalıştırma**

### Hızlı Başlatma (Önerilen)
```bash
# Başlatma script'ini çalıştırılabilir yap
chmod +x run.sh

# Uygulamayı başlat
./run.sh
```

### Manuel Başlatma
```bash
# Virtual environment'ı aktifleştir
source venv/bin/activate

# Uygulamayı çalıştır
python fcm_sender.py
```

## 📱 Token Yapısı

### Yeni Birleşik Yapı (device_tokens.json)
```json
{
  "proje1-firebase": {
    "project_id": "proje1-12345",
    "display_name": "proje1-firebase (proje1-12345)",
    "tokens": {
      "iPhone": {
        "Ali_iPhone": {
          "token": "fYz7x8...",
          "name": "Ali'nin iPhone",
          "created": "2024-01-01T10:00:00"
        },
        "Test_iOS": {
          "token": "aB3kL9...",
          "name": "Test iOS Cihazı",
          "created": "2024-01-02T14:30:00"
        }
      },
      "Android": {
        "Ayse_Samsung": {
          "token": "nM5pQ2...",
          "name": "Ayşe'nin Samsung",
          "created": "2024-01-01T11:15:00"
        }
      },
      "iPad": {},
      "Web": {},
      "Test": {}
    }
  }
}
```

## 🎯 Kullanım

### 1. Ana Menü
```
🔥 İNTERAKTİF FCM BİLDİRİM GÖNDERİCİ
1. 📱 Bildirim Gönder
2. 🔧 Token Yönetimi  
3. 🗂️  Firebase Proje Yönetimi
4. 📊 Durumu Göster
5. 📋 Logları Görüntüle
6. ❌ Çıkış
```

### 2. Token Yönetimi
- **Token Görüntüleme**: Tüm projelerdeki token'ları listele
- **Token Ekleme**: Yeni token ekle ve ad ver
- **Token Silme**: Mevcut token'ları sil
- **Token Adı Değiştirme**: Token adlarını düzenle
- **Proje Ekleme/Silme**: Yeni projeler ekle veya mevcut projeleri sil

### 3. Bildirim Gönderimi
1. **Proje Seçimi**: Hangi Firebase projesini kullanacağınızı seçin
2. **Gönderim Türü**: Token'lara veya Topic'e gönderim seçin
3. **Kategori Seçimi**: iPhone, Android, vb. kategorilerden seçim
4. **Bildirim Detayları**: Başlık, mesaj ve ek veriler

### 4. Log İzleme
- **Bugünkü Loglar**: Güncel aktiviteler
- **Başarısız Token'lar**: Gönderim başarısız olan token'lar
- **Kritik Hatalar**: Sistem hataları
- **Topic Hataları**: Topic gönderim hataları

## 🔍 Özellik Detayları

### Token Adlandırma
```
Varsayılan: iPhone_1, Android_1, iPad_1
Özel: "Ali'nin iPhone", "Test Cihazı", "Prototip Android"
```

### Hata Türleri
- **UnregisteredError**: Token artık geçerli değil
- **SenderIdMismatchError**: Proje yapılandırma hatası
- **QuotaExceededError**: Gönderim kotası aşıldı
- **Other**: Diğer hatalar

### Platform Ayarları
- **Android**: High priority, default sound, default channel
- **iOS**: Priority 10, default sound, badge counter

## 🛠️ Geliştirici Notları

### Eski Yapıdan Yeniye Dönüşüm
Uygulama eski token yapısını otomatik olarak algılar ve yeni yapıya dönüştürür:
```python
# Eski yapı algılandığında
if isinstance(data, dict) and "iPhone" in data:
    self._convert_old_structure(data)
```

### Logging Sistemi
- **Günlük Dosyalar**: Her gün için ayrı log dosyası
- **JSON Formatı**: Hata raporları JSON formatında
- **UTF-8 Encoding**: Türkçe karakter desteği

### Hata İşleme
```python
# Detaylı hata analizi
self._process_detailed_response(response, tokens, project_id, title, body)
```

## �� Sorun Giderme

### Script Sorunları

#### setup.sh Hataları
1. **Python Bulunamadı**: 
   ```bash
   # Python 3.7+ yükleyin
   brew install python3  # macOS
   sudo apt install python3  # Ubuntu/Debian
   ```

2. **Permission Denied**:
   ```bash
   chmod +x setup.sh
   ```

3. **Virtual Environment Hatası**:
   ```bash
   # Mevcut venv'i silin ve tekrar deneyin
   rm -rf venv
   ./setup.sh
   ```

#### run.sh Hataları
1. **Virtual Environment Bulunamadı**:
   ```bash
   # setup.sh'yi önce çalıştırın
   ./setup.sh
   ```

2. **Python Modül Hatası**:
   ```bash
   # Bağımlılıkları yeniden yükleyin
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Firebase Bağlantı Hataları
1. JSON key dosyalarının doğru klasörde olduğunu kontrol edin
2. Firebase projekt ayarlarını kontrol edin
3. Internet bağlantınızı kontrol edin

### Token Hataları
1. Token'ların geçerli olduğunu kontrol edin
2. Proje-token eşleştirmelerini kontrol edin
3. Log dosyalarından detaylı hata bilgilerini inceleyin

### Log Dosyaları
- `logs/` klasöründeki dosyaları inceleyin
- Kritik hatalar için `critical_errors_*.json` dosyalarına bakın
- Başarısız token'lar için `failed_tokens_*.json` dosyalarını kontrol edin

## 📄 Lisans

Bu proje MIT lisansı altında yayınlanmıştır.

## 👨‍💻 Geliştirici

Firebase Cloud Messaging entegrasyonu ile geliştirilmiş Python uygulaması.

---

**Not**: Bu uygulama Firebase Admin SDK kullanır ve server-to-server iletişim sağlar. Client-side token'lar ile çalışır ve güvenli bir şekilde bildirim gönderir.

