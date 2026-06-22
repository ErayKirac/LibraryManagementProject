"""
cli/menuler.py
------------
Her bölüm (kitaplar, üyeler, ödünç) için alt menü fonksiyonları.
Kullanıcı girdisini alır, model fonksiyonlarını çağırır, sonucu gösterir.
"""

import sqlite3
from cli import goruntu as d
from models import kitap_model as bm
from models import uye_model   as mm
from models import odunc_model as brm


# ─── Giriş Yardımcıları ───────────────────────────────────────────────────────

def _input(prompt: str) -> str:
    """Kullanıcıdan giriş alır (boşluk temizler)."""
    return input(f"  {prompt}").strip()


def _input_int(prompt: str, required: bool = True) -> int | None:
    """Sayısal giriş alır; boş bırakılabilir (required=False)."""
    val = _input(prompt)
    if not val and not required:
        return None
    try:
        return int(val)
    except ValueError:
        d.error("Geçersiz sayı. Lütfen tam sayı girin.")
        return None


def _confirm(prompt: str) -> bool:
    """E/H onayı alır."""
    return _input(f"{prompt} (e/H): ").lower() in ("e", "evet", "y", "yes")


# ═══════════════════════════════════════════════════════════════════════════════
# KİTAP MENÜSÜ
# ═══════════════════════════════════════════════════════════════════════════════

def books_menu(conn: sqlite3.Connection) -> None:
    """Kitap yönetimi alt menüsü."""
    while True:
        d.header("📖  Kitap Yönetimi")
        print("  [1] Tüm kitapları listele")
        print("  [2] Kitap ara")
        print("  [3] Yeni kitap ekle")
        print("  [4] Kitap güncelle")
        print("  [5] Kitap sil")
        print("  [6] Müsait kitapları listele")
        print("  [0] Ana menüye dön")
        print()
        choice = _input("Seçiminiz → ")

        if choice == "1":
            d.header("Tüm Kitaplar")
            d.print_books_table(bm.get_all_books(conn))
            d.press_enter()

        elif choice == "2":
            kw = _input("Aranacak kelime (başlık/yazar/ISBN): ")
            if kw:
                results = bm.search_books(conn, kw)
                d.header(f"Arama Sonuçları: '{kw}'")
                d.print_books_table(results)
                d.press_enter()

        elif choice == "3":
            d.header("Yeni Kitap Ekle")
            isbn   = _input("ISBN                : ")
            title  = _input("Kitap adı           : ")
            author = _input("Yazar               : ")
            genre  = _input("Tür (boş=Genel)     : ") or "Genel"
            year   = _input_int("Yayın yılı (boş ok): ", required=False)
            copies = _input_int("Kopya sayısı (boş=1): ", required=False) or 1

            if not isbn or not title or not author:
                d.error("ISBN, başlık ve yazar alanları zorunludur.")
                continue

            try:
                book_id = bm.add_book(conn, isbn, title, author, genre, year, copies)
                d.success(f"Kitap eklendi! (ID: {book_id})")
            except sqlite3.IntegrityError:
                d.error("Bu ISBN zaten kayıtlı.")

        elif choice == "4":
            d.header("Kitap Güncelle")
            book_id = _input_int("Güncellenecek kitap ID: ")
            if book_id is None:
                continue
            book = bm.get_book_by_id(conn, book_id)
            if not book:
                d.error(f"ID={book_id} ile kitap bulunamadı.")
                continue

            d.info(f"Mevcut: '{book['title']}' / {book['author']}")
            d.info("Boş bırakılan alanlar değişmeyecek.")
            title  = _input("Yeni başlık  : ") or None
            author = _input("Yeni yazar   : ") or None
            genre  = _input("Yeni tür     : ") or None
            year   = _input_int("Yeni yıl     : ", required=False)
            copies = _input_int("Yeni kopya # : ", required=False)

            if bm.update_book(conn, book_id, title, author, genre, year, copies):
                d.success("Kitap güncellendi.")
            else:
                d.error("Güncelleme başarısız.")

        elif choice == "5":
            d.header("Kitap Sil")
            book_id = _input_int("Silinecek kitap ID: ")
            if book_id is None:
                continue
            book = bm.get_book_by_id(conn, book_id)
            if not book:
                d.error(f"ID={book_id} ile kitap bulunamadı.")
                continue

            d.warning(f"'{book['title']}' silinecek. Bu işlem geri alınamaz!")
            if _confirm("Onaylıyor musunuz?"):
                if bm.delete_book(conn, book_id):
                    d.success("Kitap silindi.")
                else:
                    d.error("Bu kitap şu an ödünçte, silinemez.")

        elif choice == "6":
            d.header("Müsait Kitaplar")
            d.print_books_table(bm.get_available_books(conn))
            d.press_enter()

        elif choice == "0":
            break
        else:
            d.warning("Geçersiz seçim.")


# ═══════════════════════════════════════════════════════════════════════════════
# ÜYE MENÜSÜ
# ═══════════════════════════════════════════════════════════════════════════════

def members_menu(conn: sqlite3.Connection) -> None:
    """Üye yönetimi alt menüsü."""
    while True:
        d.header("👤  Üye Yönetimi")
        print("  [1] Tüm üyeleri listele")
        print("  [2] Üye ara")
        print("  [3] Yeni üye ekle")
        print("  [4] Üye bilgilerini güncelle")
        print("  [5] Üye pasifleştir")
        print("  [6] Üye sil (geçmişi yoksa)")
        print("  [7] Üyenin ödünç geçmişi")
        print("  [0] Ana menüye dön")
        print()
        choice = _input("Seçiminiz → ")

        if choice == "1":
            d.header("Tüm Üyeler")
            d.print_members_table(mm.get_all_members(conn))
            d.press_enter()

        elif choice == "2":
            kw = _input("Aranacak kelime (ad/e-posta/telefon): ")
            if kw:
                d.header(f"Arama: '{kw}'")
                d.print_members_table(mm.search_members(conn, kw))
                d.press_enter()

        elif choice == "3":
            d.header("Yeni Üye Ekle")
            name    = _input("Ad Soyad              : ")
            email   = _input("E-posta               : ")
            phone   = _input("Telefon (boş ok)      : ") or None
            address = _input("Adres   (boş ok)      : ") or None

            if not name or not email:
                d.error("Ad ve e-posta zorunludur.")
                continue
            try:
                mid = mm.add_member(conn, name, email, phone, address)
                d.success(f"Üye eklendi! (ID: {mid})")
            except sqlite3.IntegrityError:
                d.error("Bu e-posta adresi zaten kayıtlı.")

        elif choice == "4":
            d.header("Üye Güncelle")
            mid = _input_int("Güncellenecek üye ID: ")
            if mid is None:
                continue
            member = mm.get_member_by_id(conn, mid)
            if not member:
                d.error(f"ID={mid} ile üye bulunamadı.")
                continue

            d.info(f"Mevcut: {member['name']} / {member['email']}")
            d.info("Boş bırakılan alanlar değişmeyecek.")
            name    = _input("Yeni ad     : ") or None
            email   = _input("Yeni e-posta: ") or None
            phone   = _input("Yeni telefon: ") or None
            address = _input("Yeni adres  : ") or None

            try:
                if mm.update_member(conn, mid, name, email, phone, address):
                    d.success("Üye güncellendi.")
                else:
                    d.error("Güncelleme başarısız.")
            except sqlite3.IntegrityError:
                d.error("Bu e-posta başka bir üyeye ait.")

        elif choice == "5":
            d.header("Üye Pasifleştir")
            mid = _input_int("Pasifleştirilecek üye ID: ")
            if mid is None:
                continue
            if mm.deactivate_member(conn, mid):
                d.success("Üye pasifleştirildi.")
            else:
                d.error("Üye bulunamadı veya aktif ödünç kaydı var.")

        elif choice == "6":
            d.header("Üye Sil")
            mid = _input_int("Silinecek üye ID: ")
            if mid is None:
                continue
            if _confirm("Bu işlem geri alınamaz. Emin misiniz?"):
                if mm.delete_member(conn, mid):
                    d.success("Üye silindi.")
                else:
                    d.error("Üyenin geçmiş ödünç kayıtları var; silinemiyor. Pasifleştirmeyi deneyin.")

        elif choice == "7":
            d.header("Üye Ödünç Geçmişi")
            mid = _input_int("Üye ID: ")
            if mid is None:
                continue
            member = mm.get_member_by_id(conn, mid)
            if not member:
                d.error("Üye bulunamadı.")
                continue
            d.info(f"Üye: {member['name']}")
            records = mm.get_member_borrow_history(conn, mid)
            d.print_borrows_table(records, show_return=True)
            d.press_enter()

        elif choice == "0":
            break
        else:
            d.warning("Geçersiz seçim.")


# ═══════════════════════════════════════════════════════════════════════════════
# ÖDÜNÇ MENÜSÜ
# ═══════════════════════════════════════════════════════════════════════════════

def borrow_menu(conn: sqlite3.Connection) -> None:
    """Ödünç alma/iade alt menüsü."""
    while True:
        d.header("🔄  Ödünç İşlemleri")
        print("  [1] Kitap ödünç ver")
        print("  [2] Kitap iade al")
        print("  [3] Aktif ödünç kayıtları")
        print("  [4] Gecikmiş kayıtlar")
        print("  [5] Tüm ödünç geçmişi")
        print("  [0] Ana menüye dön")
        print()
        choice = _input("Seçiminiz → ")

        if choice == "1":
            d.header("Kitap Ödünç Ver")
            book_id   = _input_int("Kitap ID   : ")
            member_id = _input_int("Üye ID     : ")
            if book_id is None or member_id is None:
                continue
            result = brm.borrow_book(conn, book_id, member_id)
            if result["success"]:
                d.success(f"Kitap ödünç verildi! İade tarihi: {result['due_date']} (Kayıt ID: {result['record_id']})")
            else:
                d.error(result["error"])

        elif choice == "2":
            d.header("Kitap İade Al")
            record_id = _input_int("Ödünç kayıt ID: ")
            if record_id is None:
                continue
            result = brm.return_book(conn, record_id)
            if result["success"]:
                d.success(f"İade işlemi tamamlandı. ({result['return_date']})")
                if result["overdue_days"] > 0:
                    d.warning(f"Kitap {result['overdue_days']} gün geç iade edildi!")
            else:
                d.error(result["error"])

        elif choice == "3":
            d.header("Aktif Ödünç Kayıtları")
            d.print_borrows_table(brm.get_active_borrows(conn))
            d.press_enter()

        elif choice == "4":
            d.header("Gecikmiş Kayıtlar")
            brm.update_overdue_statuses(conn)  # Otomatik güncelle
            d.print_overdue_table(brm.get_overdue_borrows(conn))
            d.press_enter()

        elif choice == "5":
            d.header("Tüm Ödünç Geçmişi")
            d.print_borrows_table(brm.get_all_borrows(conn), show_return=True)
            d.press_enter()

        elif choice == "0":
            break
        else:
            d.warning("Geçersiz seçim.")
