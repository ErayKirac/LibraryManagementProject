"""
models/odunc_model.py
----------------------
Ödünç alma (borrow_records) tablosu için işlemler:
  - Kitap ödünç verme
  - Kitap iade alma
  - Gecikmiş kayıtları güncelleme
  - Aktif ve geçmiş ödünç listesi
"""

import sqlite3
from datetime import date, timedelta
from typing import Optional

# Ödünç alma süresi (gün)
BORROW_DAYS = 14


# ─── CREATE (Ödünç Ver) ───────────────────────────────────────────────────────

def borrow_book(conn: sqlite3.Connection,
                book_id: int,
                member_id: int) -> dict:
    """
    Kitap ödünç verme işlemi.
    Kontroller:
      1. Kitap mevcut mu? (available > 0)
      2. Üye aktif mi?
      3. Aynı üye bu kitabı zaten ödünçte tutuyor mu?
    Başarılı olursa {'success': True, 'record_id': id, 'due_date': ...} döner.
    Başarısız olursa {'success': False, 'error': mesaj} döner.
    """
    # 1. Kitap kontrolü
    book = conn.execute(
        "SELECT * FROM books WHERE id=?", (book_id,)
    ).fetchone()
    if not book:
        return {"success": False, "error": "Kitap bulunamadı."}
    if book["available"] < 1:
        return {"success": False, "error": f"'{book['title']}' şu an mevcut değil (tüm kopyalar ödünçte)."}

    # 2. Üye kontrolü
    member = conn.execute(
        "SELECT * FROM members WHERE id=?", (member_id,)
    ).fetchone()
    if not member:
        return {"success": False, "error": "Üye bulunamadı."}
    if not member["is_active"]:
        return {"success": False, "error": "Pasif üyeye kitap verilemez."}

    # 3. Çift ödünç kontrolü
    already = conn.execute(
        """SELECT id FROM borrow_records
           WHERE book_id=? AND member_id=? AND status='borrowed'""",
        (book_id, member_id)
    ).fetchone()
    if already:
        return {"success": False, "error": "Bu üye zaten bu kitabı ödünçte tutuyor."}

    # Tarihler
    borrow_date = date.today().isoformat()
    due_date    = (date.today() + timedelta(days=BORROW_DAYS)).isoformat()

    # Ödünç kaydı oluştur
    cursor = conn.execute(
        """INSERT INTO borrow_records (book_id, member_id, borrow_date, due_date, status)
           VALUES (?, ?, ?, ?, 'borrowed')""",
        (book_id, member_id, borrow_date, due_date)
    )
    # Mevcut kopya sayısını azalt
    conn.execute(
        "UPDATE books SET available = available - 1 WHERE id=?", (book_id,)
    )
    conn.commit()
    return {"success": True, "record_id": cursor.lastrowid, "due_date": due_date}


# ─── UPDATE (İade Al) ─────────────────────────────────────────────────────────

def return_book(conn: sqlite3.Connection, record_id: int) -> dict:
    """
    Kitap iade işlemi.
    - Kaydı 'returned' olarak işaretler.
    - Gerçek iade tarihini kaydeder.
    - Kitabın 'available' sayısını artırır.
    """
    record = conn.execute(
        "SELECT * FROM borrow_records WHERE id=?", (record_id,)
    ).fetchone()

    if not record:
        return {"success": False, "error": "Ödünç kaydı bulunamadı."}
    if record["status"] == "returned":
        return {"success": False, "error": "Bu kitap zaten iade edilmiş."}

    return_date = date.today().isoformat()
    conn.execute(
        """UPDATE borrow_records
           SET return_date=?, status='returned'
           WHERE id=?""",
        (return_date, record_id)
    )
    conn.execute(
        "UPDATE books SET available = available + 1 WHERE id=?",
        (record["book_id"],)
    )
    conn.commit()

    # Gecikme bilgisi
    due = date.fromisoformat(record["due_date"])
    today = date.today()
    overdue_days = max(0, (today - due).days)

    return {
        "success": True,
        "return_date": return_date,
        "overdue_days": overdue_days
    }


# ─── READ ─────────────────────────────────────────────────────────────────────

def get_active_borrows(conn: sqlite3.Connection) -> list:
    """Şu an ödünçte olan tüm kitapları üye ve kitap bilgileriyle döndürür."""
    return conn.execute(
        """SELECT br.id, b.title, b.author, m.name AS member_name,
                  br.borrow_date, br.due_date, br.status
           FROM   borrow_records br
           JOIN   books   b ON b.id = br.book_id
           JOIN   members m ON m.id = br.member_id
           WHERE  br.status IN ('borrowed', 'overdue')
           ORDER BY br.due_date"""
    ).fetchall()


def get_overdue_borrows(conn: sqlite3.Connection) -> list:
    """
    Gecikmiş kayıtları döndürür.
    Hem 'overdue' statüslü kayıtları hem de due_date geçmiş 'borrowed' kayıtlarını
    kontrol eder (güncellenmiş statüs olsun ya da olmasın).
    """
    today = date.today().isoformat()
    return conn.execute(
        """SELECT br.id, b.title, m.name AS member_name, m.email,
                  br.borrow_date, br.due_date,
                  julianday('now') - julianday(br.due_date) AS overdue_days
           FROM   borrow_records br
           JOIN   books   b ON b.id = br.book_id
           JOIN   members m ON m.id = br.member_id
           WHERE  br.status != 'returned'
             AND  br.due_date < ?
           ORDER BY br.due_date""",
        (today,)
    ).fetchall()


def get_all_borrows(conn: sqlite3.Connection) -> list:
    """Tüm ödünç kayıtlarını (iade edilenler dahil) döndürür."""
    return conn.execute(
        """SELECT br.id, b.title, m.name AS member_name,
                  br.borrow_date, br.due_date, br.return_date, br.status
           FROM   borrow_records br
           JOIN   books   b ON b.id = br.book_id
           JOIN   members m ON m.id = br.member_id
           ORDER BY br.borrow_date DESC"""
    ).fetchall()


# ─── Gecikme Statüsü Güncelleme ───────────────────────────────────────────────

def update_overdue_statuses(conn: sqlite3.Connection) -> int:
    """
    İade tarihi geçmiş 'borrowed' kayıtlarını otomatik olarak 'overdue' yapar.
    Güncellenen kayıt sayısını döndürür.
    """
    today = date.today().isoformat()
    cursor = conn.execute(
        """UPDATE borrow_records
           SET    status = 'overdue'
           WHERE  status = 'borrowed'
             AND  due_date < ?""",
        (today,)
    )
    conn.commit()
    return cursor.rowcount
