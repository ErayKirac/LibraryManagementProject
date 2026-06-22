"""
tests/test_library.py
---------------------
Kütüphane Yönetim Sistemi — Test Paketi

Testler geçici bir bellek-içi (in-memory) SQLite veritabanı kullanır;
gerçek library.db dosyasına dokunulmaz.

Çalıştırmak için:
    python -m pytest tests/ -v
    veya
    python tests/test_library.py
"""

import sys
import os
import sqlite3
import unittest
from datetime import date, timedelta

# Proje kök dizinini import yoluna ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.kitap_model import (add_book, get_all_books, get_book_by_id,
                                  search_books, update_book, delete_book,
                                  get_available_books)
from models.uye_model   import (add_member, get_all_members, get_member_by_id,
                                  search_members, update_member,
                                  deactivate_member, delete_member,
                                  get_member_borrow_history)
from models.odunc_model import (borrow_book, return_book, get_active_borrows,
                                  get_overdue_borrows, update_overdue_statuses)


# ─── Test Veritabanı Kurulumu ─────────────────────────────────────────────────

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            "database", "sema.sql")


def create_test_db() -> sqlite3.Connection:
    """
    Her test için temiz, bellekte saklanan geçici bir veritabanı oluşturur.
    Sadece tablo yapıları oluşturulur; örnek veri yüklenmez.
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    # Tabloları doğrudan oluştur — SQL dosyasını parse etmeye gerek yok
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn        TEXT    UNIQUE NOT NULL,
            title       TEXT    NOT NULL,
            author      TEXT    NOT NULL,
            genre       TEXT    DEFAULT 'Genel',
            year        INTEGER,
            copies      INTEGER NOT NULL DEFAULT 1,
            available   INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS members (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            phone       TEXT,
            address     TEXT,
            joined_at   TEXT    DEFAULT (datetime('now','localtime')),
            is_active   INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS borrow_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id         INTEGER NOT NULL,
            member_id       INTEGER NOT NULL,
            borrow_date     TEXT    NOT NULL DEFAULT (date('now','localtime')),
            due_date        TEXT    NOT NULL,
            return_date     TEXT    DEFAULT NULL,
            status          TEXT    NOT NULL DEFAULT 'borrowed',
            FOREIGN KEY (book_id)   REFERENCES books(id)   ON DELETE RESTRICT,
            FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE RESTRICT
        );
    """)
    return conn


# ═══════════════════════════════════════════════════════════════════════════════
# KİTAP TESTLERİ
# ═══════════════════════════════════════════════════════════════════════════════

class TestBookModel(unittest.TestCase):

    def setUp(self):
        self.conn = create_test_db()

    def tearDown(self):
        self.conn.close()

    # ── CREATE ────────────────────────────────────────────────────────────────

    def test_add_book_basic(self):
        """Temel kitap ekleme."""
        book_id = add_book(self.conn, "9781234567890", "Test Kitabı", "Test Yazar")
        self.assertIsInstance(book_id, int)
        self.assertGreater(book_id, 0)

    def test_add_book_with_all_fields(self):
        """Tüm alanlarla kitap ekleme."""
        bid = add_book(self.conn, "9780000000001", "Tam Kitap", "Yazar A",
                       genre="Roman", year=2023, copies=3)
        book = get_book_by_id(self.conn, bid)
        self.assertEqual(book["title"],  "Tam Kitap")
        self.assertEqual(book["author"], "Yazar A")
        self.assertEqual(book["copies"], 3)
        self.assertEqual(book["available"], 3)   # available == copies başlangıçta

    def test_add_duplicate_isbn_raises(self):
        """Aynı ISBN ile iki kez kitap eklenemez."""
        add_book(self.conn, "9780000000002", "Kitap 1", "Yazar")
        with self.assertRaises(sqlite3.IntegrityError):
            add_book(self.conn, "9780000000002", "Kitap 2", "Yazar")

    # ── READ ──────────────────────────────────────────────────────────────────

    def test_get_all_books_empty(self):
        """Boş veritabanında liste boş dönmeli."""
        self.assertEqual(get_all_books(self.conn), [])

    def test_get_all_books(self):
        """Eklenen kitaplar listelenmeli."""
        add_book(self.conn, "9780000000003", "A Kitabı", "Yazar 1")
        add_book(self.conn, "9780000000004", "B Kitabı", "Yazar 2")
        books = get_all_books(self.conn)
        self.assertEqual(len(books), 2)

    def test_get_book_by_id_found(self):
        """ID ile kitap bulunmalı."""
        bid = add_book(self.conn, "9780000000005", "Bulunan Kitap", "Yazar")
        book = get_book_by_id(self.conn, bid)
        self.assertIsNotNone(book)
        self.assertEqual(book["title"], "Bulunan Kitap")

    def test_get_book_by_id_not_found(self):
        """Var olmayan ID None döndürmeli."""
        self.assertIsNone(get_book_by_id(self.conn, 9999))

    def test_search_books_by_title(self):
        """Başlığa göre arama."""
        add_book(self.conn, "9780000000006", "Python Programlama", "Guido")
        add_book(self.conn, "9780000000007", "Java Temelleri",     "Duke")
        results = search_books(self.conn, "python")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Python Programlama")

    def test_search_books_by_author(self):
        """Yazara göre arama."""
        add_book(self.conn, "9780000000008", "Kitap X", "Orhan Pamuk")
        results = search_books(self.conn, "pamuk")
        self.assertEqual(len(results), 1)

    def test_search_books_no_result(self):
        """Sonuç yoksa boş liste dönmeli."""
        results = search_books(self.conn, "xyzzyx_bulunmaz")
        self.assertEqual(results, [])

    def test_get_available_books(self):
        """Yalnızca müsait kitaplar listelenmeli."""
        bid1 = add_book(self.conn, "9780000000009", "Müsait",  "Yazar", copies=2)
        bid2 = add_book(self.conn, "9780000000010", "Müsait Değil", "Yazar", copies=1)
        # bid2'yi müsait değil yap
        self.conn.execute("UPDATE books SET available=0 WHERE id=?", (bid2,))
        avail = get_available_books(self.conn)
        titles = [b["title"] for b in avail]
        self.assertIn("Müsait", titles)
        self.assertNotIn("Müsait Değil", titles)

    # ── UPDATE ────────────────────────────────────────────────────────────────

    def test_update_book_title(self):
        """Kitap başlığı güncellenmeli."""
        bid = add_book(self.conn, "9780000000011", "Eski Başlık", "Yazar")
        update_book(self.conn, bid, title="Yeni Başlık")
        self.assertEqual(get_book_by_id(self.conn, bid)["title"], "Yeni Başlık")

    def test_update_book_copies_adjusts_available(self):
        """Kopya sayısı artınca available de artmalı."""
        bid = add_book(self.conn, "9780000000012", "Kopya Test", "Yazar", copies=2)
        update_book(self.conn, bid, copies=5)
        book = get_book_by_id(self.conn, bid)
        self.assertEqual(book["copies"], 5)
        self.assertEqual(book["available"], 5)

    def test_update_book_not_found(self):
        """Var olmayan kitap güncellemesi False dönmeli."""
        result = update_book(self.conn, 9999, title="Yok")
        self.assertFalse(result)

    # ── DELETE ────────────────────────────────────────────────────────────────

    def test_delete_book_success(self):
        """Ödünçte olmayan kitap silinebilmeli."""
        bid = add_book(self.conn, "9780000000013", "Silinecek", "Yazar")
        self.assertTrue(delete_book(self.conn, bid))
        self.assertIsNone(get_book_by_id(self.conn, bid))

    def test_delete_book_not_found(self):
        """Var olmayan kitap False dönmeli."""
        self.assertFalse(delete_book(self.conn, 9999))


# ═══════════════════════════════════════════════════════════════════════════════
# ÜYE TESTLERİ
# ═══════════════════════════════════════════════════════════════════════════════

class TestMemberModel(unittest.TestCase):

    def setUp(self):
        self.conn = create_test_db()

    def tearDown(self):
        self.conn.close()

    def test_add_member_basic(self):
        """Temel üye ekleme."""
        mid = add_member(self.conn, "Ali Veli", "ali@test.com")
        self.assertGreater(mid, 0)

    def test_add_duplicate_email_raises(self):
        """Aynı e-posta ile iki üye eklenemez."""
        add_member(self.conn, "Ali", "ali@test.com")
        with self.assertRaises(sqlite3.IntegrityError):
            add_member(self.conn, "Veli", "ali@test.com")

    def test_get_member_by_id(self):
        """ID ile üye bulunmalı."""
        mid = add_member(self.conn, "Fatma", "fatma@test.com", phone="0500")
        member = get_member_by_id(self.conn, mid)
        self.assertEqual(member["name"], "Fatma")
        self.assertEqual(member["phone"], "0500")

    def test_search_members(self):
        """Ada göre arama."""
        add_member(self.conn, "Ahmet Yılmaz", "ahmet@test.com")
        add_member(self.conn, "Mehmet Kaya",  "mehmet@test.com")
        results = search_members(self.conn, "Ahmet")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Ahmet Yılmaz")

    def test_update_member(self):
        """Üye telefonu güncellenebilmeli."""
        mid = add_member(self.conn, "Test Üye", "test@test.com")
        update_member(self.conn, mid, phone="0599999999")
        self.assertEqual(get_member_by_id(self.conn, mid)["phone"], "0599999999")

    def test_deactivate_member(self):
        """Aktif ödüncü olmayan üye pasifleştirilebilmeli."""
        mid = add_member(self.conn, "Pasif Üye", "pasif@test.com")
        self.assertTrue(deactivate_member(self.conn, mid))
        self.assertEqual(get_member_by_id(self.conn, mid)["is_active"], 0)

    def test_delete_member_no_history(self):
        """Geçmişi olmayan üye silinebilmeli."""
        mid = add_member(self.conn, "Silinecek Üye", "sil@test.com")
        self.assertTrue(delete_member(self.conn, mid))
        self.assertIsNone(get_member_by_id(self.conn, mid))


# ═══════════════════════════════════════════════════════════════════════════════
# ÖDÜNÇ TESTLERİ
# ═══════════════════════════════════════════════════════════════════════════════

class TestBorrowModel(unittest.TestCase):

    def setUp(self):
        self.conn = create_test_db()
        # Test kitabı ve üyesi
        self.book_id   = add_book(self.conn, "9789990000001", "Test Kitap", "Yazar", copies=2)
        self.member_id = add_member(self.conn, "Test Üye", "testborrow@test.com")

    def tearDown(self):
        self.conn.close()

    def test_borrow_book_success(self):
        """Başarılı ödünç verme."""
        result = borrow_book(self.conn, self.book_id, self.member_id)
        self.assertTrue(result["success"])
        self.assertIn("record_id", result)
        self.assertIn("due_date",  result)

    def test_borrow_reduces_available(self):
        """Ödünç verme 'available' sayısını azaltmalı."""
        before = get_book_by_id(self.conn, self.book_id)["available"]
        borrow_book(self.conn, self.book_id, self.member_id)
        after = get_book_by_id(self.conn, self.book_id)["available"]
        self.assertEqual(after, before - 1)

    def test_borrow_book_not_found(self):
        """Var olmayan kitap için hata döndürmeli."""
        result = borrow_book(self.conn, 9999, self.member_id)
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_borrow_member_not_found(self):
        """Var olmayan üye için hata döndürmeli."""
        result = borrow_book(self.conn, self.book_id, 9999)
        self.assertFalse(result["success"])

    def test_borrow_unavailable_book(self):
        """Müsait olmayan kitap ödünç verilemez."""
        # 2 kopya var, 2 kez ödünç ver
        mid2 = add_member(self.conn, "Üye 2", "uye2@test.com")
        borrow_book(self.conn, self.book_id, self.member_id)
        borrow_book(self.conn, self.book_id, mid2)
        # 3. kez deneyelim
        mid3 = add_member(self.conn, "Üye 3", "uye3@test.com")
        result = borrow_book(self.conn, self.book_id, mid3)
        self.assertFalse(result["success"])

    def test_duplicate_borrow_prevented(self):
        """Aynı kitabı aynı üye iki kez ödünç alamaz."""
        borrow_book(self.conn, self.book_id, self.member_id)
        result = borrow_book(self.conn, self.book_id, self.member_id)
        self.assertFalse(result["success"])

    def test_return_book_success(self):
        """Başarılı iade işlemi."""
        res = borrow_book(self.conn, self.book_id, self.member_id)
        ret = return_book(self.conn, res["record_id"])
        self.assertTrue(ret["success"])
        self.assertEqual(ret["return_date"], date.today().isoformat())

    def test_return_increases_available(self):
        """İade 'available' sayısını geri artırmalı."""
        res   = borrow_book(self.conn, self.book_id, self.member_id)
        after_borrow = get_book_by_id(self.conn, self.book_id)["available"]
        return_book(self.conn, res["record_id"])
        after_return = get_book_by_id(self.conn, self.book_id)["available"]
        self.assertEqual(after_return, after_borrow + 1)

    def test_return_already_returned(self):
        """Zaten iade edilmiş kaydı tekrar iade edemez."""
        res = borrow_book(self.conn, self.book_id, self.member_id)
        return_book(self.conn, res["record_id"])
        ret2 = return_book(self.conn, res["record_id"])
        self.assertFalse(ret2["success"])

    def test_return_not_found(self):
        """Var olmayan kayıt iadesi False dönmeli."""
        result = return_book(self.conn, 9999)
        self.assertFalse(result["success"])

    def test_get_active_borrows(self):
        """Aktif ödünç listesi doğru çalışmalı."""
        borrow_book(self.conn, self.book_id, self.member_id)
        actives = get_active_borrows(self.conn)
        self.assertEqual(len(actives), 1)

    def test_update_overdue_statuses(self):
        """Vadesi geçmiş kayıtlar 'overdue' olarak işaretlenmeli."""
        res = borrow_book(self.conn, self.book_id, self.member_id)
        # due_date'i geçmişe al
        past_date = (date.today() - timedelta(days=5)).isoformat()
        self.conn.execute(
            "UPDATE borrow_records SET due_date=? WHERE id=?",
            (past_date, res["record_id"])
        )
        count = update_overdue_statuses(self.conn)
        self.assertEqual(count, 1)

    def test_get_overdue_borrows(self):
        """Gecikmiş kayıtlar listesi dolu olmalı."""
        res = borrow_book(self.conn, self.book_id, self.member_id)
        past_date = (date.today() - timedelta(days=3)).isoformat()
        self.conn.execute(
            "UPDATE borrow_records SET due_date=? WHERE id=?",
            (past_date, res["record_id"])
        )
        overdue = get_overdue_borrows(self.conn)
        self.assertGreaterEqual(len(overdue), 1)

    def test_borrow_history(self):
        """Üye ödünç geçmişi dolu dönmeli."""
        from models.uye_model   import get_member_borrow_history
        borrow_book(self.conn, self.book_id, self.member_id)
        history = get_member_borrow_history(self.conn, self.member_id)
        self.assertEqual(len(history), 1)


# ─── Çalıştırıcı ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
