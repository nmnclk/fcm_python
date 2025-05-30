#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
İnteraktif FCM Bildirim Gönderme Uygulaması
Birden çok Firebase projesi için bildirim gönderme
"""

import os
import json
import sys
import logging
from datetime import datetime
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, messaging
from typing import Dict, List, Optional

class FCMSender:
    def __init__(self):
        self.firebase_keys_dir = Path("firebase_keys")
        self.tokens_file = Path("device_tokens.json")
        self.logs_dir = Path("logs")
        self.current_app = None
        self.available_projects = {}
        self.device_tokens = {}
        
        # Klasörleri oluştur
        self.firebase_keys_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Logging sistemini kur
        self.setup_logging()
        
        # Mevcut projeleri yükle
        self.load_available_projects()
        
        # Cihaz token'larını yükle (yeni yapı)
        self.load_device_tokens()
    
    def setup_logging(self):
        """Logging sistemini kur"""
        log_file = self.logs_dir / f"fcm_log_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Logger'ı yapılandır
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("FCM Sender başlatıldı")
    
    def load_device_tokens(self):
        """Cihaz token'larını JSON dosyasından yükle - Yeni yapı"""
        if self.tokens_file.exists():
            try:
                with open(self.tokens_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Eski yapıyı yeni yapıya dönüştür
                if isinstance(data, dict) and "iPhone" in data:
                    self.logger.info("Eski token yapısı algılandı, yeniye dönüştürülüyor...")
                    self._convert_old_structure(data)
                else:
                    self.device_tokens = data
                
                total_tokens = sum(len(project_data.get('tokens', {})) for project_data in self.device_tokens.values())
                self.logger.info(f"Token yapısı yüklendi: {total_tokens} token")
            except Exception as e:
                self.logger.error(f"Token dosyası okunamadı: {e}")
                print(f"❌ Token dosyası okunamadı: {e}")
                self._create_default_structure()
        else:
            self._create_default_structure()
    
    def _create_default_structure(self):
        """Varsayılan token yapısını oluştur"""
        self.device_tokens = {}
        self.save_device_tokens()
        self.logger.info("Yeni token yapısı oluşturuldu")
    
    def _convert_old_structure(self, old_data):
        """Eski token yapısını yeniye dönüştür"""
        self.device_tokens = {}
        
        # Mevcut projeleri al
        if self.available_projects:
            first_project = list(self.available_projects.keys())[0]
            project_id = self.available_projects[first_project]['project_id']
            
            self.device_tokens[first_project] = {
                'project_id': project_id,
                'display_name': self.available_projects[first_project]['display_name'],
                'tokens': {
                    'iPhone': {},
                    'Android': {},
                    'iPad': {},
                    'Web': {},
                    'Test': {}
                }
            }
            
            # Eski token'ları yeni yapıya taşı
            for category, tokens in old_data.items():
                if category in ['iPhone', 'Android', 'iPad', 'Web', 'Test']:
                    for i, token in enumerate(tokens):
                        token_name = f"{category}_{i+1}"
                        self.device_tokens[first_project]['tokens'][category][token_name] = {
                            'token': token,
                            'name': token_name,
                            'created': datetime.now().isoformat()
                        }
        
        self.save_device_tokens()
        self.logger.info("Eski yapı yeni yapıya dönüştürüldü")
    
    def save_device_tokens(self):
        """Cihaz token'larını JSON dosyasına kaydet"""
        try:
            with open(self.tokens_file, 'w', encoding='utf-8') as f:
                json.dump(self.device_tokens, f, indent=2, ensure_ascii=False)
            self.logger.info("Token yapısı kaydedildi")
        except Exception as e:
            self.logger.error(f"Token dosyası kaydedilemedi: {e}")
            print(f"❌ Token dosyası kaydedilemedi: {e}")
    
    def show_main_menu(self):
        """Ana menüyü göster"""
        print("\n" + "="*60)
        print("🔥 İNTERAKTİF FCM BİLDİRİM GÖNDERİCİ")
        print("="*60)
        print("1. 📱 Bildirim Gönder")
        print("2. 🔧 Token Yönetimi")
        print("3. 🗂️  Firebase Proje Yönetimi")
        print("4. 📊 Durumu Göster")
        print("5. 📋 Logları Görüntüle")
        print("6. ❌ Çıkış")
        print("="*60)
    
    def show_project_selection(self) -> Optional[str]:
        """Proje seçim menüsünü göster"""
        if not self.available_projects:
            print("\n❌ Hiç Firebase projesi bulunamadı!")
            print("🔧 firebase_keys/ klasörüne JSON key dosyalarını ekleyin.")
            return None
        
        print("\n🗂️  MEVCUT PROJELERİ:")
        print("-" * 50)
        
        project_list = list(self.available_projects.keys())
        for i, project_key in enumerate(project_list, 1):
            project = self.available_projects[project_key]
            print(f"{i}. {project['display_name']}")
        
        print("-" * 50)
        
        try:
            choice = int(input("📌 Proje seçin (numara): ")) - 1
            if 0 <= choice < len(project_list):
                return project_list[choice]
            else:
                print("❌ Geçersiz seçim!")
                return None
        except ValueError:
            print("❌ Lütfen geçerli bir numara girin!")
            return None
    
    def initialize_firebase(self, project_key: str) -> bool:
        """Firebase'i seçilen proje ile başlat"""
        try:
            # Mevcut uygulamayı temizle
            if self.current_app:
                firebase_admin.delete_app(self.current_app)
                self.logger.info("Önceki Firebase uygulaması temizlendi")
            
            project = self.available_projects[project_key]
            cred = credentials.Certificate(str(project['file_path']))
            self.current_app = firebase_admin.initialize_app(cred)
            
            print(f"✅ Firebase başlatıldı: {project['display_name']}")
            self.logger.info(f"Firebase başlatıldı - Proje: {project['project_id']}, Dosya: {project['file_path']}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Firebase başlatılamadı: {error_msg}")
            self.logger.error(f"Firebase başlatılamadı - Proje: {project_key}, Hata: {error_msg}")
            return False
    
    def show_device_categories(self) -> List[str]:
        """Proje seçip o projenin token'larını göster ve seçim yap"""
        if not self.device_tokens:
            print("❌ Hiç proje ve token bulunamadı!")
            return []
        
        # Önce proje seç
        project_key = self.show_project_selection()
        if not project_key or project_key not in self.device_tokens:
            return []
        
        project_data = self.device_tokens[project_key]
        project_id = project_data.get('project_id', 'Bilinmeyen')
        tokens = project_data.get('tokens', {})
        
        print(f"\n📱 {project_data.get('display_name', project_key)} TOKEN'LARI:")
        print("-" * 80)
        
        all_tokens = []
        token_map = {}
        
        # Tüm token'ları tek listede topla
        for category, category_tokens in tokens.items():
            for token_name, token_data in category_tokens.items():
                all_tokens.append({
                    'category': category,
                    'name': token_data.get('name', token_name),
                    'token': token_data['token'],
                    'full_key': f"{project_key}:{category}:{token_name}"
                })
        
        if not all_tokens:
            print("❌ Bu projede hiç token bulunamadı!")
            return []
        
        # Token'ları numaralı liste olarak göster
        for i, token_info in enumerate(all_tokens, 1):
            token_map[i] = token_info['full_key']
            
            # Token'ın ilk ve son 6 karakterini göster
            token = token_info['token']
            if len(token) > 12:
                token_preview = f"{token[:6]}...{token[-6:]}"
            else:
                token_preview = token
            
            print(f"  {i}. [{token_info['category']}] {token_info['name']}")
            print(f"     📱 {token_preview}")
        
        print(f"\n{len(all_tokens) + 1}. Tümü")
        print("-" * 80)
        
        try:
            choice = input("📌 Token seçin (numara veya birden çok numara virgülle): ")
            choices = [int(x.strip()) for x in choice.split(',')]
            
            selected_tokens = []
            for c in choices:
                if c == len(all_tokens) + 1:  # Tümü seçeneği
                    return [token_info['full_key'] for token_info in all_tokens]
                elif 1 <= c <= len(all_tokens):
                    selected_tokens.append(token_map[c])
            
            return selected_tokens if selected_tokens else []
            
        except (ValueError, IndexError):
            print("❌ Geçersiz seçim!")
            return []
    
    def get_tokens_from_categories(self, categories: List[str]) -> List[str]:
        """Seçilen token'lardan token değerlerini al"""
        all_tokens = []
        for token_full in categories:
            try:
                parts = token_full.split(':', 2)  # project_key:category:token_name
                if len(parts) == 3:
                    project_key, category, token_name = parts
                    if project_key in self.device_tokens:
                        category_tokens = self.device_tokens[project_key]['tokens'].get(category, {})
                        if token_name in category_tokens:
                            all_tokens.append(category_tokens[token_name]['token'])
            except ValueError:
                continue
        return [token for token in all_tokens if token.strip()]
    
    def get_token_details_from_categories(self, categories: List[str]) -> Dict[str, List[Dict]]:
        """Seçilen token'lardan token detaylarını al"""
        token_details = {}
        for token_full in categories:
            try:
                parts = token_full.split(':', 2)  # project_key:category:token_name
                if len(parts) == 3:
                    project_key, category, token_name = parts
                    if project_key in self.device_tokens:
                        category_tokens = self.device_tokens[project_key]['tokens'].get(category, {})
                        if token_name in category_tokens:
                            category_key = f"{project_key}:{category}"
                            if category_key not in token_details:
                                token_details[category_key] = []
                            
                            token_data = category_tokens[token_name]
                            token_details[category_key].append({
                                'name': token_data.get('name', token_name),
                                'token': token_data['token']
                            })
            except ValueError:
                continue
        return token_details
    
    def send_notification(self):
        """Bildirim gönderme işlemi"""
        # Gönderim türünü seç
        print("\n📤 GÖNDERİM TÜRÜ:")
        print("-" * 30)
        print("1. Token'lara Gönder")
        print("2. Topic'e Gönder")
        print("-" * 30)
        
        try:
            send_type = int(input("Gönderim türü seçin: "))
            if send_type == 1:
                self._send_to_tokens()
            elif send_type == 2:
                self._send_to_topic()
            else:
                print("❌ Geçersiz seçim!")
        except ValueError:
            print("❌ Geçerli bir numara girin!")
    
    def _send_to_tokens(self):
        """Token'lara bildirim gönder"""
        # Token seçimi (içinde proje seçimi de var)
        selected_tokens = self.show_device_categories()
        if not selected_tokens:
            print("❌ Hiç token seçilmedi!")
            return
        
        # Seçilen token'lardan proje bilgisini al
        project_key = selected_tokens[0].split(':')[0]  # İlk token'dan proje bilgisini al
        
        if project_key not in self.available_projects:
            print("❌ Proje bulunamadı!")
            return
        
        # Firebase'i başlat
        if not self.initialize_firebase(project_key):
            return
        
        project_info = self.available_projects[project_key]
        project_id = project_info['project_id']
        
        tokens = self.get_tokens_from_categories(selected_tokens)
        token_details = self.get_token_details_from_categories(selected_tokens)
        
        if not tokens:
            print("❌ Hiç token bulunamadı!")
            self.logger.warning(f"Proje {project_id} için token bulunamadı")
            return
        
        # Token'ları bu proje ile eşleştir (gerekirse proje oluştur)
        if project_key not in self.device_tokens:
            self.device_tokens[project_key] = {
                'project_id': project_id,
                'display_name': project_info['display_name'],
                'tokens': {
                    'iPhone': {},
                    'Android': {},
                    'iPad': {},
                    'Web': {},
                    'Test': {}
                }
            }
            self.save_device_tokens()
        
        print(f"\n📤 {len(tokens)} cihaza bildirim gönderilecek")
        print(f"🗂️  Proje: {project_info['display_name']}")
        
        # Seçilen token'ların detaylarını göster
        if token_details:
            print(f"\n📱 Seçilen Cihazlar:")
            for category_key, category_token_list in token_details.items():
                project_name, category_name = category_key.split(':', 1)
                print(f"   🏷️  {category_name}:")
                for token_info in category_token_list:
                    print(f"      • {token_info['name']}")
        
        # Bildirim detaylarını al
        notification_data = self._get_notification_details()
        if not notification_data:
            return
        
        title, body, data, android_priority, ios_priority, sound = notification_data
        
        # Log başlangıcı
        self.logger.info(f"Token bildirim gönderme başlatıldı - Proje: {project_id}, Token sayısı: {len(tokens)}")
        self.logger.info(f"Başlık: {title}, Mesaj: {body}")
        if data:
            self.logger.info(f"Ek veriler: {data}")
        
        # Seçilen token adlarını da logla
        for category_key, category_token_list in token_details.items():
            project_name, category_name = category_key.split(':', 1)
            token_names = [token_info['name'] for token_info in category_token_list]
            self.logger.info(f"Seçilen {category_name} token'ları: {', '.join(token_names)}")
        
        # Bildirimi gönder
        try:
            # Gelişmiş mesaj konfigürasyonu
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                android=messaging.AndroidConfig(
                    priority=android_priority,
                    notification=messaging.AndroidNotification(
                        sound=sound,
                        channel_id='default'
                    ),
                ),
                apns=messaging.APNSConfig(
                    headers={'apns-priority': ios_priority},
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound=sound,
                            badge=1
                        )
                    ),
                ),
                data=data if data else None,
                tokens=tokens
            )
            
            # send_each_for_multicast kullanarak daha detaylı sonuç al
            response = messaging.send_each_for_multicast(message)
            
            print(f"\n✅ Bildirim gönderildi!")
            print(f"📊 Başarılı: {response.success_count}")
            print(f"❌ Başarısız: {response.failure_count}")
            
            # Başarılı gönderim logu
            self.logger.info(f"Token bildirim gönderildi - Başarılı: {response.success_count}, Başarısız: {response.failure_count}")
            
            # Detaylı hata analizi
            self._process_detailed_response(response, tokens, project_id, title, body)
        
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Bildirim gönderilemedi: {error_msg}")
            
            # Detaylı hata logu
            self.logger.error(f"KRITIK HATA - Token bildirim gönderilemedi")
            self.logger.error(f"Proje: {project_id}")
            self.logger.error(f"Hata: {error_msg}")
            self.logger.error(f"Token sayısı: {len(tokens)}")
            
            # Hata detaylarını ayrı dosyaya kaydet
            self._save_critical_error(project_id, error_msg, tokens, title, body, data)
    
    def _send_to_topic(self):
        """Topic'e bildirim gönder"""
        # Proje seç
        project_key = self.show_project_selection()
        if not project_key:
            return
        
        # Firebase'i başlat
        if not self.initialize_firebase(project_key):
            return
        
        project_info = self.available_projects[project_key]
        project_id = project_info['project_id']
        
        print(f"\n📡 Topic'e bildirim gönderimi")
        print(f"🗂️  Proje: {project_info['display_name']}")
        
        topic = input("📌 Topic adı: ").strip()
        if not topic:
            print("❌ Topic adı boş olamaz!")
            return
        
        # Bildirim detaylarını al
        notification_data = self._get_notification_details()
        if not notification_data:
            return
        
        title, body, data, android_priority, ios_priority, sound = notification_data
        
        # Log başlangıcı
        self.logger.info(f"Topic bildirim gönderme başlatıldı - Proje: {project_id}, Topic: {topic}")
        self.logger.info(f"Başlık: {title}, Mesaj: {body}")
        
        try:
            # Topic mesajı konfigürasyonu
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                android=messaging.AndroidConfig(
                    priority=android_priority,
                    notification=messaging.AndroidNotification(
                        sound=sound,
                        channel_id='default'
                    ),
                ),
                apns=messaging.APNSConfig(
                    headers={'apns-priority': ios_priority},
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound=sound,
                            badge=1
                        )
                    ),
                ),
                data=data if data else None,
                topic=topic
            )
            
            response = messaging.send(message)
            
            print(f"\n✅ Topic bildirimi gönderildi!")
            print(f"📡 Topic: {topic}")
            print(f"📋 Mesaj ID: {response}")
            
            self.logger.info(f"Topic bildirim başarılı - Topic: {topic}, Mesaj ID: {response}")
        
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Topic bildirimi gönderilemedi: {error_msg}")
            
            self.logger.error(f"KRITIK HATA - Topic bildirim gönderilemedi")
            self.logger.error(f"Proje: {project_id}")
            self.logger.error(f"Topic: {topic}")
            self.logger.error(f"Hata: {error_msg}")
            
            # Topic hata kaydetme
            self._save_topic_error(project_id, topic, error_msg, title, body, data)
    
    def _get_notification_details(self):
        """Bildirim detaylarını kullanıcıdan al"""
        print("📝 Bildirim detaylarını girin:")
        
        # Temel bilgiler
        title = input("📰 Başlık: ").strip()
        body = input("💬 Mesaj: ").strip()
        
        if not title or not body:
            print("❌ Başlık ve mesaj boş olamaz!")
            self.logger.warning("Boş başlık veya mesaj nedeniyle bildirim gönderilmedi")
            return None
        
        # Varsayılan ayarlar
        android_priority = 'high'
        ios_priority = '10'
        sound = 'default'
        
        # Ek veriler (isteğe bağlı)
        print("\n🔧 Ek veriler (isteğe bağlı - Enter ile geç):")
        data = {}
        while True:
            key = input("Anahtar: ").strip()
            if not key:
                break
            value = input(f"Değer ({key}): ").strip()
            if value:
                data[key] = value
        
        return title, body, data, android_priority, ios_priority, sound
    
    def _process_detailed_response(self, response, tokens, project_id, title, body):
        """Detaylı yanıt işleme"""
        if response.failure_count > 0:
            print("\n❌ Başarısız olan token'lar:")
            failed_tokens = []
            unregistered_tokens = []
            sender_mismatch_tokens = []
            quota_exceeded_tokens = []
            other_error_tokens = []
            
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    failed_token = tokens[idx]
                    error_msg = str(resp.exception) if resp.exception else "Bilinmeyen hata"
                    
                    print(f"  - {failed_token[:50]}... : {error_msg}")
                    
                    # Hata türüne göre kategorilere ayır
                    if isinstance(resp.exception, messaging.UnregisteredError):
                        unregistered_tokens.append(failed_token)
                        self.logger.warning(f"Token artık kayıtlı değil: {failed_token[:50]}...")
                    elif isinstance(resp.exception, messaging.SenderIdMismatchError):
                        sender_mismatch_tokens.append(failed_token)
                        self.logger.error(f"Sender ID hatası: {failed_token[:50]}...")
                    elif isinstance(resp.exception, messaging.QuotaExceededError):
                        quota_exceeded_tokens.append(failed_token)
                        self.logger.error(f"Kota aşıldı: {failed_token[:50]}...")
                    else:
                        other_error_tokens.append(failed_token)
                        self.logger.error(f"Diğer hata - Token: {failed_token[:50]}..., Hata: {error_msg}")
                    
                    failed_tokens.append({
                        'token': failed_token,
                        'error': error_msg,
                        'error_type': type(resp.exception).__name__ if resp.exception else 'Unknown',
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Kategorilere göre rapor
            if unregistered_tokens:
                print(f"\n🚫 Kayıtlı olmayan token'lar: {len(unregistered_tokens)}")
                print("💡 Bu token'ları temizlemeniz önerilir.")
            
            if sender_mismatch_tokens:
                print(f"\n⚠️  Sender ID hatası olan token'lar: {len(sender_mismatch_tokens)}")
                print("💡 Firebase proje ayarlarınızı kontrol edin.")
            
            if quota_exceeded_tokens:
                print(f"\n📊 Kota aşan token'lar: {len(quota_exceeded_tokens)}")
                print("💡 Firebase planınızı kontrol edin.")
            
            # Başarısız token'ları kaydet
            self._save_failed_tokens(project_id, failed_tokens, title, body)
        
        # Başarılı token'ları kaydet
        successful_tokens = []
        for idx, resp in enumerate(response.responses):
            if resp.success:
                successful_tokens.append(tokens[idx])
        
        if successful_tokens:
            self.logger.info(f"Başarılı token'lar ({len(successful_tokens)} adet)")
            for token in successful_tokens:
                self.logger.info(f"  Başarılı token: {token[:50]}...")
    
    def _save_failed_tokens(self, project_id: str, failed_tokens: List[dict], title: str, body: str):
        """Başarısız token'ları dosyaya kaydet"""
        try:
            failed_file = self.logs_dir / f"failed_tokens_{datetime.now().strftime('%Y%m%d')}.json"
            
            failed_data = {
                'timestamp': datetime.now().isoformat(),
                'project_id': project_id,
                'notification': {
                    'title': title,
                    'body': body
                },
                'failed_tokens': failed_tokens
            }
            
            # Mevcut dosyayı oku
            existing_data = []
            if failed_file.exists():
                with open(failed_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            existing_data.append(failed_data)
            
            # Dosyaya kaydet
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Başarısız token'lar kaydedildi: {failed_file}")
            
        except Exception as e:
            self.logger.error(f"Başarısız token'lar kaydedilemedi: {e}")
    
    def _save_topic_error(self, project_id: str, topic: str, error_msg: str, title: str, body: str, data: dict):
        """Topic hatasını kaydet"""
        try:
            error_file = self.logs_dir / f"topic_errors_{datetime.now().strftime('%Y%m%d')}.json"
            
            error_data = {
                'timestamp': datetime.now().isoformat(),
                'project_id': project_id,
                'topic': topic,
                'error_message': error_msg,
                'notification': {
                    'title': title,
                    'body': body,
                    'data': data
                }
            }
            
            # Mevcut dosyayı oku
            existing_data = []
            if error_file.exists():
                with open(error_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            existing_data.append(error_data)
            
            # Dosyaya kaydet
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Topic hatası kaydedildi: {error_file}")
            
        except Exception as e:
            self.logger.error(f"Topic hatası kaydedilemedi: {e}")
    
    def _save_critical_error(self, project_id: str, error_msg: str, tokens: List[str], title: str, body: str, data: dict):
        """Kritik hataları dosyaya kaydet"""
        try:
            error_file = self.logs_dir / f"critical_errors_{datetime.now().strftime('%Y%m%d')}.json"
            
            error_data = {
                'timestamp': datetime.now().isoformat(),
                'project_id': project_id,
                'error_message': error_msg,
                'notification': {
                    'title': title,
                    'body': body,
                    'data': data
                },
                'token_count': len(tokens),
                'tokens': [token[:50] + '...' for token in tokens]  # Sadece ilk 50 karakter
            }
            
            # Mevcut dosyayı oku
            existing_data = []
            if error_file.exists():
                with open(error_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            existing_data.append(error_data)
            
            # Dosyaya kaydet
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Kritik hata kaydedildi: {error_file}")
            
        except Exception as e:
            self.logger.error(f"Kritik hata kaydedilemedi: {e}")
    
    def manage_tokens(self):
        """Token yönetimi menüsü"""
        while True:
            print("\n🔧 CİHAZ TOKEN YÖNETİMİ")
            print("-" * 40)
            print("1. Token'ları Görüntüle")
            print("2. Token Ekle")
            print("3. Token Sil")
            print("4. Token Adını Değiştir")
            print("5. Yeni Proje Ekle")
            print("6. Proje Sil")
            print("7. Ana Menüye Dön")
            print("-" * 40)
            
            choice = input("Seçiminiz: ").strip()
            
            if choice == "1":
                self.show_all_tokens()
            elif choice == "2":
                self.add_token()
            elif choice == "3":
                self.remove_token()
            elif choice == "4":
                self.rename_token()
            elif choice == "5":
                self.add_project()
            elif choice == "6":
                self.remove_project()
            elif choice == "7":
                break
            else:
                print("❌ Geçersiz seçim!")
    
    def show_all_tokens(self):
        """Tüm token'ları göster"""
        print("\n📱 TÜM CİHAZ TOKEN'LARI:")
        print("=" * 80)
        
        if not self.device_tokens:
            print("❌ Hiç proje ve token bulunamadı!")
            return
        
        for project_key, project_data in self.device_tokens.items():
            project_id = project_data.get('project_id', 'Bilinmeyen')
            display_name = project_data.get('display_name', project_key)
            tokens = project_data.get('tokens', {})
            
            print(f"\n🗂️  {display_name}")
            print(f"   Proje Key: {project_key}")
            print(f"   Proje ID: {project_id}")
            
            total_tokens = sum(len(category_tokens) for category_tokens in tokens.values())
            print(f"   Toplam Token: {total_tokens}")
            
            for category, category_tokens in tokens.items():
                print(f"\n   🏷️  {category} ({len(category_tokens)} token):")
                if category_tokens:
                    for token_name, token_data in category_tokens.items():
                        created = token_data.get('created', 'Bilinmeyen')[:19]
                        print(f"      • {token_data.get('name', token_name)}")
                        print(f"        Token: {token_data['token'][:50]}...")
                        print(f"        Oluşturulma: {created}")
                else:
                    print("      (Boş)")
    
    def add_token(self):
        """Token ekle"""
        # Önce proje seç
        project_key = self._select_project_for_token()
        if not project_key:
            return
        
        # Kategori seç
        categories = ['iPhone', 'Android', 'iPad', 'Web', 'Test']
        print("\n📱 Kategoriler:")
        for i, category in enumerate(categories, 1):
            existing_count = len(self.device_tokens[project_key]['tokens'].get(category, {}))
            print(f"{i}. {category} ({existing_count} mevcut token)")
        
        try:
            choice = int(input("Kategori seçin: ")) - 1
            if 0 <= choice < len(categories):
                category = categories[choice]
                
                # Token bilgilerini al
                token = input("\nToken girin: ").strip()
                if not token:
                    print("❌ Token boş olamaz!")
                    return
                
                # Token adı
                default_name = f"{category}_{len(self.device_tokens[project_key]['tokens'][category]) + 1}"
                token_name = input(f"Token adı (varsayılan: {default_name}): ").strip()
                if not token_name:
                    token_name = default_name
                
                # Token'ın zaten var olup olmadığını kontrol et
                existing_tokens = {}
                for cat_tokens in self.device_tokens[project_key]['tokens'].values():
                    existing_tokens.update(cat_tokens)
                
                for existing_token_data in existing_tokens.values():
                    if existing_token_data['token'] == token:
                        print(f"❌ Bu token zaten mevcut: {existing_token_data['name']}")
                        return
                
                # Token'ı ekle
                if category not in self.device_tokens[project_key]['tokens']:
                    self.device_tokens[project_key]['tokens'][category] = {}
                
                self.device_tokens[project_key]['tokens'][category][token_name] = {
                    'token': token,
                    'name': token_name,
                    'created': datetime.now().isoformat()
                }
                
                self.save_device_tokens()
                print(f"✅ Token '{token_name}' {category} kategorisine eklendi!")
                self.logger.info(f"Yeni token eklendi - Proje: {project_key}, Kategori: {category}, Ad: {token_name}")
            else:
                print("❌ Geçersiz kategori!")
        except ValueError:
            print("❌ Geçerli bir numara girin!")
    
    def _select_project_for_token(self):
        """Token işlemleri için proje seç"""
        if not self.device_tokens:
            print("\n❌ Hiç proje bulunamadı! Önce bir proje ekleyin.")
            return None
        
        print("\n🗂️  Projeler:")
        project_keys = list(self.device_tokens.keys())
        for i, project_key in enumerate(project_keys, 1):
            project_data = self.device_tokens[project_key]
            display_name = project_data.get('display_name', project_key)
            print(f"{i}. {display_name}")
        
        print(f"{len(project_keys) + 1}. Yeni Proje Ekle")
        
        try:
            choice = int(input("Proje seçin: ")) - 1
            if choice == len(project_keys):
                return self.add_project()
            elif 0 <= choice < len(project_keys):
                return project_keys[choice]
            else:
                print("❌ Geçersiz seçim!")
                return None
        except ValueError:
            print("❌ Geçerli bir numara girin!")
            return None
    
    def add_project(self):
        """Yeni proje ekle"""
        if not self.available_projects:
            print("❌ Hiç Firebase projesi bulunamadı!")
            print("🔧 firebase_keys/ klasörüne JSON key dosyalarını ekleyin.")
            return None
        
        # Henüz eklenmemiş projeleri bul
        available_keys = []
        for project_key, project_info in self.available_projects.items():
            if project_key not in self.device_tokens:
                available_keys.append(project_key)
        
        if not available_keys:
            print("❌ Tüm Firebase projeleri zaten eklenmiş!")
            return None
        
        print("\n🗂️  Eklenebilir Projeler:")
        for i, project_key in enumerate(available_keys, 1):
            project_info = self.available_projects[project_key]
            print(f"{i}. {project_info['display_name']}")
        
        try:
            choice = int(input("Eklenecek proje: ")) - 1
            if 0 <= choice < len(available_keys):
                project_key = available_keys[choice]
                project_info = self.available_projects[project_key]
                
                self.device_tokens[project_key] = {
                    'project_id': project_info['project_id'],
                    'display_name': project_info['display_name'],
                    'tokens': {
                        'iPhone': {},
                        'Android': {},
                        'iPad': {},
                        'Web': {},
                        'Test': {}
                    }
                }
                
                self.save_device_tokens()
                print(f"✅ Proje eklendi: {project_info['display_name']}")
                self.logger.info(f"Yeni proje eklendi: {project_key}")
                return project_key
            else:
                print("❌ Geçersiz seçim!")
                return None
        except ValueError:
            print("❌ Geçerli bir numara girin!")
            return None
    
    def remove_token(self):
        """Token sil"""
        project_key = self._select_project_for_token()
        if not project_key:
            return
        
        tokens = self.device_tokens[project_key]['tokens']
        
        # Tüm token'ları listele
        all_tokens = []
        for category, category_tokens in tokens.items():
            for token_name, token_data in category_tokens.items():
                all_tokens.append({
                    'category': category,
                    'name': token_name,
                    'token': token_data['token'],
                    'display': f"{category} - {token_data['name']}"
                })
        
        if not all_tokens:
            print("❌ Bu projede hiç token yok!")
            return
        
        print(f"\n📱 {self.device_tokens[project_key]['display_name']} Token'ları:")
        for i, token_info in enumerate(all_tokens, 1):
            print(f"{i}. {token_info['display']}")
            print(f"   {token_info['token'][:50]}...")
        
        try:
            choice = int(input("Silinecek token numarası: ")) - 1
            if 0 <= choice < len(all_tokens):
                token_info = all_tokens[choice]
                
                confirm = input(f"'{token_info['display']}' token'ını silmek istediğinizden emin misiniz? (evet/hayır): ")
                if confirm.lower() in ['evet', 'e', 'yes', 'y']:
                    del self.device_tokens[project_key]['tokens'][token_info['category']][token_info['name']]
                    self.save_device_tokens()
                    print(f"✅ Token silindi: {token_info['display']}")
                    self.logger.info(f"Token silindi - Proje: {project_key}, Token: {token_info['name']}")
                else:
                    print("❌ İşlem iptal edildi!")
            else:
                print("❌ Geçersiz token numarası!")
        except ValueError:
            print("❌ Geçerli bir numara girin!")
    
    def rename_token(self):
        """Token adını değiştir"""
        project_key = self._select_project_for_token()
        if not project_key:
            return
        
        tokens = self.device_tokens[project_key]['tokens']
        
        # Tüm token'ları listele
        all_tokens = []
        for category, category_tokens in tokens.items():
            for token_name, token_data in category_tokens.items():
                all_tokens.append({
                    'category': category,
                    'name': token_name,
                    'data': token_data,
                    'display': f"{category} - {token_data['name']}"
                })
        
        if not all_tokens:
            print("❌ Bu projede hiç token yok!")
            return
        
        print(f"\n📱 {self.device_tokens[project_key]['display_name']} Token'ları:")
        for i, token_info in enumerate(all_tokens, 1):
            print(f"{i}. {token_info['display']}")
        
        try:
            choice = int(input("Adı değiştirilecek token numarası: ")) - 1
            if 0 <= choice < len(all_tokens):
                token_info = all_tokens[choice]
                current_name = token_info['data']['name']
                
                new_name = input(f"Yeni ad (şu anki: {current_name}): ").strip()
                if not new_name:
                    print("❌ Yeni ad boş olamaz!")
                    return
                
                # Eski anahtarı sil, yeni anahtarla ekle
                old_data = self.device_tokens[project_key]['tokens'][token_info['category']][token_info['name']]
                del self.device_tokens[project_key]['tokens'][token_info['category']][token_info['name']]
                
                old_data['name'] = new_name
                self.device_tokens[project_key]['tokens'][token_info['category']][new_name] = old_data
                
                self.save_device_tokens()
                print(f"✅ Token adı değiştirildi: {current_name} → {new_name}")
                self.logger.info(f"Token adı değiştirildi - Proje: {project_key}, Eski: {current_name}, Yeni: {new_name}")
            else:
                print("❌ Geçersiz token numarası!")
        except ValueError:
            print("❌ Geçerli bir numara girin!")
    
    def remove_project(self):
        """Proje sil"""
        if not self.device_tokens:
            print("❌ Hiç proje bulunamadı!")
            return
        
        print("\n🗂️  Projeler:")
        project_keys = list(self.device_tokens.keys())
        for i, project_key in enumerate(project_keys, 1):
            project_data = self.device_tokens[project_key]
            display_name = project_data.get('display_name', project_key)
            total_tokens = sum(len(tokens) for tokens in project_data['tokens'].values())
            print(f"{i}. {display_name} ({total_tokens} token)")
        
        try:
            choice = int(input("Silinecek proje numarası: ")) - 1
            if 0 <= choice < len(project_keys):
                project_key = project_keys[choice]
                project_data = self.device_tokens[project_key]
                display_name = project_data.get('display_name', project_key)
                
                print(f"\n⚠️  DİKKAT: '{display_name}' projesi ve tüm token'ları silinecek!")
                confirm = input("Devam etmek istediğinizden emin misiniz? (evet/hayır): ")
                
                if confirm.lower() in ['evet', 'e', 'yes', 'y']:
                    del self.device_tokens[project_key]
                    self.save_device_tokens()
                    print(f"✅ Proje silindi: {display_name}")
                    self.logger.info(f"Proje silindi: {project_key}")
                else:
                    print("❌ İşlem iptal edildi!")
            else:
                print("❌ Geçersiz proje numarası!")
        except ValueError:
            print("❌ Geçerli bir numara girin!")
    
    def manage_projects(self):
        """Firebase proje yönetimi"""
        while True:
            print("\n🗂️  FİREBASE PROJE YÖNETİMİ")
            print("-" * 40)
            print("1. Mevcut Projeleri Göster")
            print("2. Proje Tarayıcısını Yenile")
            print("3. JSON Key Klasörünü Aç")
            print("4. Ana Menüye Dön")
            print("-" * 40)
            
            choice = input("Seçiminiz: ").strip()
            
            if choice == "1":
                self.show_projects()
            elif choice == "2":
                self.load_available_projects()
                print("✅ Projeler yenilendi!")
            elif choice == "3":
                self.open_keys_folder()
            elif choice == "4":
                break
            else:
                print("❌ Geçersiz seçim!")
    
    def show_projects(self):
        """Mevcut projeleri göster"""
        print("\n🗂️  MEVCUT PROJELERİ:")
        print("=" * 60)
        
        if not self.available_projects:
            print("❌ Hiç proje bulunamadı!")
            print("🔧 firebase_keys/ klasörüne JSON key dosyalarını ekleyin.")
            return
        
        for project_key, project in self.available_projects.items():
            print(f"\n📂 {project_key}")
            print(f"   Proje ID: {project['project_id']}")
            print(f"   Dosya: {project['file_path']}")
    
    def open_keys_folder(self):
        """JSON keys klasörünü aç"""
        try:
            import subprocess
            import platform
            
            keys_path = str(self.firebase_keys_dir.absolute())
            
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", keys_path])
            elif platform.system() == "Windows":
                subprocess.run(["explorer", keys_path])
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", keys_path])
            
            print(f"✅ Klasör açıldı: {keys_path}")
            print("🔧 JSON key dosyalarınızı bu klasöre ekleyin ve proje tarayıcısını yenileyin.")
            
        except Exception as e:
            print(f"❌ Klasör açılamadı: {e}")
            print(f"📁 Manuel olarak açın: {self.firebase_keys_dir.absolute()}")
    
    def show_status(self):
        """Sistem durumunu göster"""
        print("\n📊 SİSTEM DURUMU")
        print("=" * 50)
        
        # Firebase proje sayısı
        firebase_project_count = len(self.available_projects)
        print(f"🗂️  Firebase JSON Key Dosyaları: {firebase_project_count}")
        
        if self.available_projects:
            for project_key, project in self.available_projects.items():
                status = "✅ Eklendi" if project_key in self.device_tokens else "⏳ Henüz eklenmedi"
                print(f"   • {project['display_name']} - {status}")
        
        # Eklenen proje ve token sayıları
        added_project_count = len(self.device_tokens)
        print(f"\n📱 Token Sistemi:")
        print(f"   • Eklenen proje sayısı: {added_project_count}")
        
        total_tokens = 0
        for project_key, project_data in self.device_tokens.items():
            project_total = sum(len(category_tokens) for category_tokens in project_data['tokens'].values())
            total_tokens += project_total
            display_name = project_data.get('display_name', project_key)
            
            print(f"\n   🗂️  {display_name}:")
            print(f"      Toplam token: {project_total}")
            
            for category, category_tokens in project_data['tokens'].items():
                if category_tokens:
                    print(f"      • {category}: {len(category_tokens)} token")
        
        print(f"\n📊 Genel Özet:")
        print(f"   • Toplam token sayısı: {total_tokens}")
        print(f"   • Aktif proje sayısı: {added_project_count}")
        
        # Dosya durumu
        print(f"\n📁 Dosya Durumları:")
        print(f"   • JSON Keys Klasörü: {self.firebase_keys_dir.exists()}")
        print(f"   • Token Dosyısı: {self.tokens_file.exists()}")
        print(f"   • Log Klasörü: {self.logs_dir.exists()}")
        
        # Log durumu
        today_log = self.logs_dir / f"fcm_log_{datetime.now().strftime('%Y%m%d')}.log"
        failed_log = self.logs_dir / f"failed_tokens_{datetime.now().strftime('%Y%m%d')}.json"
        error_log = self.logs_dir / f"critical_errors_{datetime.now().strftime('%Y%m%d')}.json"
        topic_log = self.logs_dir / f"topic_errors_{datetime.now().strftime('%Y%m%d')}.json"
        
        print(f"\n📋 Bugünkü Log Durumu:")
        print(f"   • Genel log: {today_log.exists()}")
        print(f"   • Başarısız token log: {failed_log.exists()}")
        print(f"   • Kritik hata log: {error_log.exists()}")
        print(f"   • Topic hata log: {topic_log.exists()}")
    
    def show_logs(self):
        """Log dosyalarını göster ve yönet"""
        while True:
            print("\n📋 LOG YÖNETİMİ")
            print("-" * 40)
            print("1. Bugünkü Logları Göster")
            print("2. Başarısız Token'ları Göster")
            print("3. Kritik Hataları Göster")
            print("4. Topic Hatalarını Göster")
            print("5. Log Dosyalarını Listele")
            print("6. Log Klasörünü Aç")
            print("7. Ana Menüye Dön")
            print("-" * 40)
            
            choice = input("Seçiminiz: ").strip()
            
            if choice == "1":
                self._show_today_logs()
            elif choice == "2":
                self._show_failed_tokens_log()
            elif choice == "3":
                self._show_critical_errors_log()
            elif choice == "4":
                self._show_topic_errors_log()
            elif choice == "5":
                self._list_log_files()
            elif choice == "6":
                self._open_logs_folder()
            elif choice == "7":
                break
            else:
                print("❌ Geçersiz seçim!")
    
    def _show_today_logs(self):
        """Bugünkü logları göster"""
        today_log = self.logs_dir / f"fcm_log_{datetime.now().strftime('%Y%m%d')}.log"
        
        if not today_log.exists():
            print("❌ Bugünkü log dosyası bulunamadı!")
            return
        
        print(f"\n📋 BUGÜNKÜ LOGLAR ({today_log.name}):")
        print("=" * 60)
        
        try:
            with open(today_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Son 50 satırı göster
            recent_lines = lines[-50:] if len(lines) > 50 else lines
            
            for line in recent_lines:
                print(line.strip())
            
            if len(lines) > 50:
                print(f"\n... (Toplam {len(lines)} satır, son 50 satır gösteriliyor)")
                
        except Exception as e:
            print(f"❌ Log dosyası okunamadı: {e}")
    
    def _show_failed_tokens_log(self):
        """Başarısız token loglarını göster"""
        failed_file = self.logs_dir / f"failed_tokens_{datetime.now().strftime('%Y%m%d')}.json"
        
        if not failed_file.exists():
            print("❌ Bugün başarısız token kaydı bulunamadı!")
            return
        
        try:
            with open(failed_file, 'r', encoding='utf-8') as f:
                failed_data = json.load(f)
            
            print(f"\n❌ BAŞARISIZ TOKEN'LAR ({failed_file.name}):")
            print("=" * 60)
            
            for entry in failed_data:
                timestamp = entry.get('timestamp', 'Bilinmeyen')
                project_id = entry.get('project_id', 'Bilinmeyen')
                notification = entry.get('notification', {})
                failed_tokens = entry.get('failed_tokens', [])
                
                print(f"\n⏰ Zaman: {timestamp}")
                print(f"🗂️  Proje: {project_id}")
                print(f"📰 Başlık: {notification.get('title', 'Bilinmeyen')}")
                print(f"💬 Mesaj: {notification.get('body', 'Bilinmeyen')}")
                print(f"❌ Başarısız Token Sayısı: {len(failed_tokens)}")
                
                for token_info in failed_tokens[:3]:  # İlk 3 hatayı göster
                    print(f"   • {token_info.get('token', '')[:50]}... : {token_info.get('error', '')}")
                
                if len(failed_tokens) > 3:
                    print(f"   ... ve {len(failed_tokens) - 3} hata daha")
                print("-" * 40)
                
        except Exception as e:
            print(f"❌ Başarısız token dosyası okunamadı: {e}")
    
    def _show_critical_errors_log(self):
        """Kritik hata loglarını göster"""
        error_file = self.logs_dir / f"critical_errors_{datetime.now().strftime('%Y%m%d')}.json"
        
        if not error_file.exists():
            print("❌ Bugün kritik hata kaydı bulunamadı! (Bu iyi bir şey 😊)")
            return
        
        try:
            with open(error_file, 'r', encoding='utf-8') as f:
                error_data = json.load(f)
            
            print(f"\n🚨 KRİTİK HATALAR ({error_file.name}):")
            print("=" * 60)
            
            for entry in error_data:
                timestamp = entry.get('timestamp', 'Bilinmeyen')
                project_id = entry.get('project_id', 'Bilinmeyen')
                error_msg = entry.get('error_message', 'Bilinmeyen')
                token_count = entry.get('token_count', 0)
                
                print(f"\n⏰ Zaman: {timestamp}")
                print(f"🗂️  Proje: {project_id}")
                print(f"🚨 Hata: {error_msg}")
                print(f"📱 Etkilenen Token Sayısı: {token_count}")
                print("-" * 40)
                
        except Exception as e:
            print(f"❌ Kritik hata dosyası okunamadı: {e}")
    
    def _show_topic_errors_log(self):
        """Topic hata loglarını göster"""
        error_file = self.logs_dir / f"topic_errors_{datetime.now().strftime('%Y%m%d')}.json"
        
        if not error_file.exists():
            print("❌ Bugün topic hata kaydı bulunamadı!")
            return
        
        try:
            with open(error_file, 'r', encoding='utf-8') as f:
                error_data = json.load(f)
            
            print(f"\n🚨 TOPIC HATALARI ({error_file.name}):")
            print("=" * 60)
            
            for entry in error_data:
                timestamp = entry.get('timestamp', 'Bilinmeyen')
                project_id = entry.get('project_id', 'Bilinmeyen')
                topic = entry.get('topic', 'Bilinmeyen')
                error_msg = entry.get('error_message', 'Bilinmeyen')
                notification = entry.get('notification', {})
                
                print(f"\n⏰ Zaman: {timestamp}")
                print(f"🗂️  Proje: {project_id}")
                print(f"🚨 Hata: {error_msg}")
                print(f"📡 Topic: {topic}")
                print(f"📰 Başlık: {notification.get('title', 'Bilinmeyen')}")
                print(f"💬 Mesaj: {notification.get('body', 'Bilinmeyen')}")
                print("-" * 40)
                
        except Exception as e:
            print(f"❌ Topic hata dosyası okunamadı: {e}")
    
    def _list_log_files(self):
        """Log dosyalarını listele"""
        print(f"\n📁 LOG DOSYALARI ({self.logs_dir}):")
        print("=" * 50)
        
        log_files = list(self.logs_dir.glob("*.log")) + list(self.logs_dir.glob("*.json"))
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not log_files:
            print("❌ Hiç log dosyası bulunamadı!")
            return
        
        for log_file in log_files:
            file_size = log_file.stat().st_size
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            size_str = f"{file_size} bytes"
            if file_size > 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            if file_size > 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            
            print(f"📄 {log_file.name}")
            print(f"   Boyut: {size_str}")
            print(f"   Tarih: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
    
    def _open_logs_folder(self):
        """Log klasörünü aç"""
        try:
            import subprocess
            import platform
            
            logs_path = str(self.logs_dir.absolute())
            
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", logs_path])
            elif platform.system() == "Windows":
                subprocess.run(["explorer", logs_path])
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", logs_path])
            
            print(f"✅ Log klasörü açıldı: {logs_path}")
            
        except Exception as e:
            print(f"❌ Klasör açılamadı: {e}")
            print(f"📁 Manuel olarak açın: {self.logs_dir.absolute()}")
    
    def load_available_projects(self):
        """Firebase JSON key dosyalarını tarayarak mevcut projeleri yükle"""
        self.available_projects = {}
        
        if not self.firebase_keys_dir.exists():
            self.logger.warning("Firebase keys klasörü bulunamadı")
            return
            
        project_count = 0
        for json_file in self.firebase_keys_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    key_data = json.load(f)
                    project_id = key_data.get('project_id', 'Bilinmeyen Proje')
                    self.available_projects[json_file.stem] = {
                        'file_path': json_file,
                        'project_id': project_id,
                        'display_name': f"{json_file.stem} ({project_id})"
                    }
                    project_count += 1
                    self.logger.info(f"Proje yüklendi: {project_id} - {json_file.name}")
            except Exception as e:
                self.logger.error(f"{json_file.name} dosyası okunamadı: {e}")
                print(f"❌ {json_file.name} dosyası okunamadı: {e}")
        
        self.logger.info(f"Toplam {project_count} proje yüklendi")
    
    def run(self):
        """Ana uygulama döngüsü"""
        try:
            while True:
                self.show_main_menu()
                choice = input("Seçiminiz: ").strip()
                
                if choice == "1":
                    self.send_notification()
                elif choice == "2":
                    self.manage_tokens()
                elif choice == "3":
                    self.manage_projects()
                elif choice == "4":
                    self.show_status()
                elif choice == "5":
                    self.show_logs()
                elif choice == "6":
                    print("👋 Görüşürüz!")
                    break
                else:
                    print("❌ Geçersiz seçim! Lütfen 1-6 arası bir sayı girin.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Uygulama sonlandırıldı!")
        
        finally:
            # Firebase uygulamasını temizle
            if self.current_app:
                try:
                    firebase_admin.delete_app(self.current_app)
                except:
                    pass

def main():
    """Ana fonksiyon"""
    # Gerekli kütüphaneleri kontrol et
    try:
        import firebase_admin
    except ImportError:
        print("❌ firebase-admin kütüphanesi bulunamadı!")
        print("🔧 Yüklemek için: pip install firebase-admin")
        return
    
    print("🔥 FCM Bildirim Gönderici başlatılıyor...")
    
    # Uygulamayı başlat
    app = FCMSender()
    app.run()

if __name__ == "__main__":
    main() 