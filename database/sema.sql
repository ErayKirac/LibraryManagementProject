-- ============================================================
-- Kütüphane Yönetim Sistemi - Veritabanı Şeması
-- ============================================================
-- Tablolar: books (kitaplar), members (üyeler), borrow_records (ödünç kayıtları)
-- İlişkiler: borrow_records -> books (kitap_id), borrow_records -> members (uye_id)
-- ============================================================

-- Kitaplar tablosu
CREATE TABLE IF NOT EXISTS books (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn        TEXT    UNIQUE NOT NULL,           -- Uluslararası Standart Kitap Numarası
    title       TEXT    NOT NULL,                  -- Kitap adı
    author      TEXT    NOT NULL,                  -- Yazar adı
    genre       TEXT    DEFAULT 'Genel',           -- Tür/Kategori
    year        INTEGER,                           -- Yayın yılı
    copies      INTEGER NOT NULL DEFAULT 1,        -- Toplam kopya sayısı
    available   INTEGER NOT NULL DEFAULT 1,        -- Mevcut (ödünç verilmemiş) kopya sayısı
    created_at  TEXT    DEFAULT (datetime('now','localtime'))
);

-- Üyeler tablosu
CREATE TABLE IF NOT EXISTS members (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,                  -- Ad Soyad
    email       TEXT    UNIQUE NOT NULL,           -- E-posta (benzersiz)
    phone       TEXT,                              -- Telefon numarası
    address     TEXT,                              -- Adres
    joined_at   TEXT    DEFAULT (datetime('now','localtime')),
    is_active   INTEGER NOT NULL DEFAULT 1         -- 1: Aktif, 0: Pasif
);

-- Ödünç alma kayıtları tablosu
CREATE TABLE IF NOT EXISTS borrow_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id         INTEGER NOT NULL,
    member_id       INTEGER NOT NULL,
    borrow_date     TEXT    NOT NULL DEFAULT (date('now','localtime')),
    due_date        TEXT    NOT NULL,              -- İade tarihi (14 gün sonra)
    return_date     TEXT    DEFAULT NULL,          -- Gerçek iade tarihi (NULL = hâlâ ödünçte)
    status          TEXT    NOT NULL DEFAULT 'borrowed',  -- 'borrowed' | 'returned' | 'overdue'
    -- Yabancı Anahtar İlişkileri
    FOREIGN KEY (book_id)   REFERENCES books(id)   ON DELETE RESTRICT,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE RESTRICT
);

-- ============================================================
-- Örnek Veriler (INSERT)
-- ============================================================

-- Örnek Kitaplar
INSERT OR IGNORE INTO books (isbn, title, author, genre, year, copies, available) VALUES
    ('9780143127796', 'Suç ve Ceza',           'Fyodor Dostoyevski', 'Roman',    1866, 3, 3),
    ('9780062316097', 'Sapiens',                'Yuval Noah Harari',  'Tarih',    2011, 2, 2),
    ('9780547928227', 'Yüzüklerin Efendisi',    'J.R.R. Tolkien',     'Fantezi',  1954, 4, 4),
    ('9780743273565', 'Muhteşem Gatsby',        'F. Scott Fitzgerald','Roman',    1925, 2, 2),
    ('9780316769174', 'Çavdar Tarlasındaki Çocuklar', 'J.D. Salinger','Roman',  1951, 3, 3),
    ('9780141439518', 'Gurur ve Önyargı',       'Jane Austen',        'Roman',    1813, 2, 2),
    ('9780385333481', 'Cesur Yeni Dünya',       'Aldous Huxley',      'Distopya', 1932, 2, 2),
    ('9780452284234', '1984',                   'George Orwell',      'Distopya', 1949, 3, 3),
    ('9780062409850', 'Dünyanın Uğultusuna Karşı', 'Elif Şafak',     'Roman',    2015, 2, 2),
    ('9789750719387', 'İnce Memed',             'Yaşar Kemal',        'Roman',    1955, 2, 2);

-- Örnek Üyeler
INSERT OR IGNORE INTO members (name, email, phone, address) VALUES
    ('Ahmet Yılmaz',   'ahmet.yilmaz@email.com',   '0532-111-2233', 'Ankara, Çankaya'),
    ('Fatma Demir',    'fatma.demir@email.com',     '0543-222-3344', 'İstanbul, Kadıköy'),
    ('Mehmet Kaya',    'mehmet.kaya@email.com',     '0554-333-4455', 'İzmir, Bornova'),
    ('Ayşe Şahin',    'ayse.sahin@email.com',       '0505-444-5566', 'Bursa, Osmangazi'),
    ('Ali Öztürk',     'ali.ozturk@email.com',      '0516-555-6677', 'Antalya, Muratpaşa');

-- Örnek Ödünç Kayıtları (bazıları iade edilmiş, bazıları devam ediyor)
INSERT OR IGNORE INTO borrow_records (book_id, member_id, borrow_date, due_date, return_date, status) VALUES
    (1, 1, date('now','-20 days'), date('now','-6 days'),  date('now','-8 days'), 'returned'),
    (2, 2, date('now','-10 days'), date('now','+4 days'),  NULL,                  'borrowed'),
    (3, 3, date('now','-5 days'),  date('now','+9 days'),  NULL,                  'borrowed'),
    (4, 4, date('now','-30 days'), date('now','-16 days'), NULL,                  'overdue'),
    (5, 5, date('now','-3 days'),  date('now','+11 days'), NULL,                  'borrowed');

-- Ödünç verilen kitapların 'available' sayısını güncelle
UPDATE books SET available = available - 1 WHERE id IN (2, 3, 4, 5);
