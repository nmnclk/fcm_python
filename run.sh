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
