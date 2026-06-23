# 📚 Kütüphane Yönetim Sistemi (Library Management System)

> Python + SQLite ile geliştirilmiş, tam CRUD destekli konsol tabanlı kütüphane yönetim uygulaması.

---

## 📋 İçindekiler

- [Proje Hakkında](#-proje-hakkında)
- [Özellikler](#-özellikler)
- [Proje Yapısı](#-proje-yapısı)
- [Veritabanı Şeması](#-veritabanı-şeması)
- [Kurulum ve Çalıştırma](#-kurulum-ve-çalıştırma)
- [Kullanım Kılavuzu](#-kullanım-kılavuzu)
- [Testler](#-testler)
- [Teknolojiler](#-teknolojiler)

---

## 🎯 Proje Hakkında

Bu proje, bir kütüphanenin günlük operasyonlarını yönetmek için geliştirilmiş bir **konsol uygulamasıdır**. Kullanıcılar;

- Kitapları ekleyip düzenleyebilir
- Üye kayıtlarını yönetebilir
- Kitap ödünç verme ve iade işlemlerini takip edebilir
- Gecikmiş iadeler hakkında uyarı alabilir

Tüm veriler kalıcı olarak bir **SQLite** veritabanında (`library.db`) saklanır.

---

## ✨ Özellikler

| Modül | Özellik |
|---|---|
| 📖 Kitaplar | Ekleme, listeleme, arama (başlık/yazar/ISBN), güncelleme, silme |
| 👤 Üyeler | Ekleme, listeleme, arama, güncelleme, pasifleştirme, silme |
| 🔄 Ödünç | Kitap verme, iade alma, aktif/gecikmiş kayıtlar, geçmiş |
| 📊 İstatistikler | Özet veritabanı istatistikleri |
| 🎨 Arayüz | ANSI renkli terminal çıktısı, tablo görünümü |
| 🛡️ Doğrulama | Çift ödünç koruması, müsaitlik kontrolü, yabancı anahtar kısıtlamaları |

---

## 🗂️ Proje Yapısı

```
library_management/
│
├── main.py                   # Uygulamanın giriş noktası
│
├── database/
│   ├── __init__.py
│   ├── baglanti.py           # Veritabanı bağlantı yöneticisi
│   └── sema.sql              # CREATE TABLE + örnek veri (INSERT)
│
├── models/
│   ├── __init__.py
│   ├── kitap_model.py        # Kitap CRUD işlemleri
│   ├── uye_model.py          # Üye CRUD işlemleri
│   └── odunc_model.py        # Ödünç alma/iade mantığı
│
├── cli/
│   ├── __init__.py
│   ├── goruntu.py            # ANSI renkli çıktı yardımcıları
│   └── menuler.py            # Kitap, üye, ödünç alt menüleri
│
├── tests/
│   ├── __init__.py
│   └── test_kutuphane.py     # 25+ birim testi (unittest)
│
├── library.db                # SQLite veritabanı (ilk çalıştırmada oluşur)
└── README.md
```

---

## 🗄️ Veritabanı Şeması

### Tablolar ve İlişkiler

```
books                           members                           borrow_records
──────────────────────          ──────────────────────            ──────────────────────────────
id          (PK)                id          (PK)                  id          (PK)
isbn        (UNIQUE)            name                              book_id     (FK → books.id)
title                           email       (UNIQUE)              member_id   (FK → members.id)
author                          phone                             borrow_date
genre                           address                           due_date
year                            joined_at                         return_date
copies                          is_active                         status      ('borrowed'|'returned'|'overdue')
available

```

**İlişkiler:**
- `borrow_records.book_id` → `books.id` (ON DELETE RESTRICT)
- `borrow_records.member_id` → `members.id` (ON DELETE RESTRICT)

---

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler

- Python **3.10+** (f-string type union `int | None` kullanılıyor)
- Harici kütüphane **gerekmez** — yalnızca Python standart kütüphanesi kullanılmıştır:
  - `sqlite3`, `datetime`, `os`, `sys`, `unittest`

### 1. Depoyu Klonlayın

```bash
git clone https://github.com/KULLANICI_ADI/library-management-system.git
cd library-management-system
```

### 2. Uygulamayı Başlatın

```bash
python main.py
```

İlk çalıştırmada:
- `library.db` dosyası otomatik oluşturulur
- Tablolar kurulur ve örnek veriler yüklenir

### 3. Testleri Çalıştırın

```bash
# unittest ile
python -m unittest tests/test_kutuphane.py -v

# veya pytest ile (pip install pytest)
python -m pytest tests/ -v
```

---

## 📖 Kullanım Kılavuzu

### Ana Menü

```
──────────────────────────────────────────────────────────────
  🏠  ANA MENÜ
──────────────────────────────────────────────────────────────
  [1] Kitap Yönetimi
  [2] Üye Yönetimi
  [3] Ödünç İşlemleri
  [4] İstatistikler
  [0] Çıkış
```

### Tipik Kullanım Akışı

1. **Kitap ekle** → Ana Menü → [1] → [3] Yeni kitap ekle
2. **Üye ekle** → Ana Menü → [2] → [3] Yeni üye ekle
3. **Kitap ödünç ver** → Ana Menü → [3] → [1] → Kitap ID ve Üye ID gir
4. **Kitap iade al** → Ana Menü → [3] → [2] → Ödünç Kayıt ID gir
5. **Gecikmiş kontrol** → Ana Menü → [3] → [4]

### Ödünç Kuralları

| Kural | Açıklama |
|---|---|
| Ödünç süresi | 14 gün |
| Çift ödünç | Aynı üye aynı kitabı iki kez alamaz |
| Müsaitlik | Tüm kopyalar ödünçteyse yeni ödünç verilemez |
| Gecikme | İade tarihi geçince durum otomatik `overdue` olur |
| Silme koruması | Ödünçte olan kitap/geçmişi olan üye silinemez |

---

## 🧪 Testler

`tests/test_kutuphane.py` dosyasında **25+ birim testi** bulunmaktadır:

| Test Sınıfı | Test Sayısı | Kapsam |
|---|---|---|
| `TestKitapModel` | 12 | Kitap CRUD + arama + müsaitlik |
| `TestUyeModel` | 7 | Üye CRUD + pasifleştirme |
| `TestOduncModel` | 12 | Ödünç verme, iade, gecikme |

Testler **bellek içi** geçici veritabanı kullanır; `library.db`'ye dokunmaz.

```bash
python -m unittest tests/test_kutuphane.py -v

# Örnek çıktı:
# test_add_book_basic ... ok
# test_borrow_book_success ... ok
# test_return_book_success ... ok
# ...
# Ran 31 tests in 0.045s
# OK
```

---

## 🛠️ Teknolojiler

| Teknoloji | Kullanım |
|---|---|
| Python 3.10+ | Ana programlama dili |
| SQLite3 | Yerleşik ilişkisel veritabanı |
| unittest | Birim test çerçevesi |
| ANSI Escape Codes | Renkli terminal çıktısı |
| Git & GitHub | Sürüm kontrolü |

---
