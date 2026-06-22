"""
models/kitap_model.py
--------------------
Kitap (books) tablosu için tüm CRUD işlemleri.
Her fonksiyon bir sqlite3.Connection alır, işlemi yapar ve sonucu döndürür.
"""

import sqlite3
from typing import Optional


# ─── CREATE ───────────────────────────────────────────────────────────────────

def add_book(conn: sqlite3.Connection,
             isbn: str,
             title: str,
             author: str,
             genre: str = "Genel",
             year: Optional[int] = None,
             copies: int = 1) -> int:
    """
    Yeni kitap ekler. Mevcut 'available' değeri otomatik olarak 'copies' değerine eşit
    başlatılır. Başarılı olursa eklenen satırın ID'sini döndürür.
    """
    sql = """
        INSERT INTO books (isbn, title, author, genre, year, copies, available)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    cursor = conn.execute(sql, (isbn, title, author, genre, year, copies, copies))
    conn.commit()
    return cursor.lastrowid


# ─── READ ─────────────────────────────────────────────────────────────────────

def get_all_books(conn: sqlite3.Connection) -> list:
    """Tüm kitapları döndürür (ID'ye göre sıralı)."""
    return conn.execute(
        "SELECT * FROM books ORDER BY id"
    ).fetchall()


def get_book_by_id(conn: sqlite3.Connection, book_id: int) -> Optional[sqlite3.Row]:
    """ID'ye göre tek bir kitap döndürür. Bulunamazsa None."""
    return conn.execute(
        "SELECT * FROM books WHERE id = ?", (book_id,)
    ).fetchone()


def search_books(conn: sqlite3.Connection, keyword: str) -> list:
    """
    Başlık, yazar veya ISBN içinde arama yapar (büyük/küçük harf duyarsız).
    """
    pattern = f"%{keyword}%"
    return conn.execute(
        """SELECT * FROM books
           WHERE title  LIKE ? OR author LIKE ? OR isbn LIKE ?
           ORDER BY id""",
        (pattern, pattern, pattern)
    ).fetchall()


def get_available_books(conn: sqlite3.Connection) -> list:
    """Yalnızca en az 1 kopyası mevcut olan kitapları döndürür."""
    return conn.execute(
        "SELECT * FROM books WHERE available > 0 ORDER BY id"
    ).fetchall()


# ─── UPDATE ───────────────────────────────────────────────────────────────────

def update_book(conn: sqlite3.Connection,
                book_id: int,
                title: Optional[str] = None,
                author: Optional[str] = None,
                genre: Optional[str] = None,
                year: Optional[int] = None,
                copies: Optional[int] = None) -> bool:
    """
    Belirtilen alanları günceller. None gönderilen alanlar değişmez.
    Başarılı olursa True, kayıt bulunamazsa False döndürür.
    """
    # Mevcut kaydı al
    book = get_book_by_id(conn, book_id)
    if not book:
        return False

    # Güncelleme için mevcut değerleri varsayılan olarak kullan
    new_title  = title  if title  is not None else book["title"]
    new_author = author if author is not None else book["author"]
    new_genre  = genre  if genre  is not None else book["genre"]
    new_year   = year   if year   is not None else book["year"]

    # Kopya sayısı değişiyorsa 'available' farkı orantılı güncelle
    if copies is not None and copies != book["copies"]:
        diff = copies - book["copies"]
        new_available = max(0, book["available"] + diff)
        new_copies = copies
    else:
        new_copies    = book["copies"]
        new_available = book["available"]

    conn.execute(
        """UPDATE books
           SET title=?, author=?, genre=?, year=?, copies=?, available=?
           WHERE id=?""",
        (new_title, new_author, new_genre, new_year, new_copies, new_available, book_id)
    )
    conn.commit()
    return True


# ─── DELETE ───────────────────────────────────────────────────────────────────

def delete_book(conn: sqlite3.Connection, book_id: int) -> bool:
    """
    Kitabı siler. Eğer kitabın aktif (iade edilmemiş) ödünç kaydı varsa
    silme işlemi reddedilir.
    """
    # Aktif ödünç kaydı kontrolü
    active = conn.execute(
        "SELECT COUNT(*) FROM borrow_records WHERE book_id=? AND status != 'returned'",
        (book_id,)
    ).fetchone()[0]

    if active > 0:
        return False  # Silinemez — ödünçte

    cursor = conn.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    return cursor.rowcount > 0
