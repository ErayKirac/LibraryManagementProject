"""
models/uye_model.py
----------------------
Üye (members) tablosu için tüm CRUD işlemleri.
"""

import sqlite3
from typing import Optional


# ─── CREATE ───────────────────────────────────────────────────────────────────

def add_member(conn: sqlite3.Connection,
               name: str,
               email: str,
               phone: Optional[str] = None,
               address: Optional[str] = None) -> int:
    """
    Yeni üye ekler. E-posta adresi benzersiz olmalıdır.
    Başarılı olursa eklenen satırın ID'sini döndürür.
    """
    sql = """
        INSERT INTO members (name, email, phone, address)
        VALUES (?, ?, ?, ?)
    """
    cursor = conn.execute(sql, (name, email, phone, address))
    conn.commit()
    return cursor.lastrowid


# ─── READ ─────────────────────────────────────────────────────────────────────

def get_all_members(conn: sqlite3.Connection) -> list:
    """Tüm aktif ve pasif üyeleri döndürür."""
    return conn.execute(
        "SELECT * FROM members ORDER BY id"
    ).fetchall()


def get_member_by_id(conn: sqlite3.Connection, member_id: int) -> Optional[sqlite3.Row]:
    """ID'ye göre tek bir üye döndürür. Bulunamazsa None."""
    return conn.execute(
        "SELECT * FROM members WHERE id = ?", (member_id,)
    ).fetchone()


def search_members(conn: sqlite3.Connection, keyword: str) -> list:
    """Ad, e-posta veya telefon içinde arama yapar."""
    pattern = f"%{keyword}%"
    return conn.execute(
        """SELECT * FROM members
           WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
           ORDER BY id""",
        (pattern, pattern, pattern)
    ).fetchall()


def get_member_borrow_history(conn: sqlite3.Connection, member_id: int) -> list:
    """
    Bir üyenin tüm ödünç geçmişini kitap bilgileriyle birlikte döndürür.
    """
    return conn.execute(
        """SELECT br.id, b.title, b.author, br.borrow_date,
                  br.due_date, br.return_date, br.status
           FROM   borrow_records br
           JOIN   books b ON b.id = br.book_id
           WHERE  br.member_id = ?
           ORDER BY br.borrow_date DESC""",
        (member_id,)
    ).fetchall()


# ─── UPDATE ───────────────────────────────────────────────────────────────────

def update_member(conn: sqlite3.Connection,
                  member_id: int,
                  name: Optional[str] = None,
                  email: Optional[str] = None,
                  phone: Optional[str] = None,
                  address: Optional[str] = None) -> bool:
    """
    Belirtilen alanları günceller. None gönderilen alanlar değişmez.
    """
    member = get_member_by_id(conn, member_id)
    if not member:
        return False

    new_name    = name    if name    is not None else member["name"]
    new_email   = email   if email   is not None else member["email"]
    new_phone   = phone   if phone   is not None else member["phone"]
    new_address = address if address is not None else member["address"]

    conn.execute(
        "UPDATE members SET name=?, email=?, phone=?, address=? WHERE id=?",
        (new_name, new_email, new_phone, new_address, member_id)
    )
    conn.commit()
    return True


def deactivate_member(conn: sqlite3.Connection, member_id: int) -> bool:
    """
    Üyeyi pasif (is_active=0) yapar. Silmek yerine pasifleştirme tercih edilir.
    Aktif ödünç kaydı varsa pasifleştirme reddedilir.
    """
    active_borrows = conn.execute(
        "SELECT COUNT(*) FROM borrow_records WHERE member_id=? AND status='borrowed'",
        (member_id,)
    ).fetchone()[0]

    if active_borrows > 0:
        return False

    cursor = conn.execute(
        "UPDATE members SET is_active=0 WHERE id=?", (member_id,)
    )
    conn.commit()
    return cursor.rowcount > 0


# ─── DELETE ───────────────────────────────────────────────────────────────────

def delete_member(conn: sqlite3.Connection, member_id: int) -> bool:
    """
    Üyeyi kalıcı olarak siler. Ödünç geçmişi olan üyeler silinemez;
    bunun yerine deactivate_member() kullanılması önerilir.
    """
    has_records = conn.execute(
        "SELECT COUNT(*) FROM borrow_records WHERE member_id=?", (member_id,)
    ).fetchone()[0]

    if has_records > 0:
        return False  # Kayıt geçmişi var, silinemiyor

    cursor = conn.execute("DELETE FROM members WHERE id=?", (member_id,))
    conn.commit()
    return cursor.rowcount > 0
