"""
main.py
-------
Kütüphane Yönetim Sistemi — Giriş Noktası
Çalıştırmak için: python main.py
"""

import sys
from database.baglanti import initialize_database, get_connection
from models.odunc_model import update_overdue_statuses
from cli import goruntu as d
from cli.menuler import books_menu, members_menu, borrow_menu


def statistics_menu(conn) -> None:
    """Özet istatistikler ekranı."""
    d.header("📊  İstatistikler")

    stats = conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM books)                                  AS total_books,
            (SELECT COALESCE(SUM(copies),0) FROM books)                   AS total_copies,
            (SELECT COALESCE(SUM(available),0) FROM books)                AS available_copies,
            (SELECT COUNT(*) FROM members)                                AS total_members,
            (SELECT COUNT(*) FROM members WHERE is_active=1)              AS active_members,
            (SELECT COUNT(*) FROM borrow_records WHERE status='borrowed') AS active_borrows,
            (SELECT COUNT(*) FROM borrow_records WHERE status='overdue')  AS overdue_borrows,
            (SELECT COUNT(*) FROM borrow_records WHERE status='returned') AS returned_books
    """).fetchone()

    print(f"""
  {'─'*40}
  📚 Kitaplar
     Toplam farklı kitap   : {d.bold(str(stats['total_books']))}
     Toplam kopya           : {d.bold(str(stats['total_copies']))}
     Mevcut (ödünç verilebilir): {d.bold(str(stats['available_copies']))}

  👤 Üyeler
     Toplam üye             : {d.bold(str(stats['total_members']))}
     Aktif üye              : {d.bold(str(stats['active_members']))}

  🔄 Ödünç Durumu
     Şu an ödünçte          : {d.bold(str(stats['active_borrows']))}
     Gecikmiş               : {d.clr(d.bold(str(stats['overdue_borrows'])), d.RED) if stats['overdue_borrows'] else d.bold('0')}
     İade edilmiş (toplam)  : {d.bold(str(stats['returned_books']))}
  {'─'*40}
""")
    input("  Devam etmek için Enter'a basın...")


def main() -> None:
    """Ana uygulama döngüsü."""
    # Veritabanını hazırla
    initialize_database()

    conn = get_connection()

    # Uygulama başlarken gecikmiş kayıtları güncelle
    updated = update_overdue_statuses(conn)
    if updated:
        d.warning(f"{updated} kayıt 'gecikmiş' olarak işaretlendi.")

    d.banner()

    try:
        while True:
            d.header("🏠  ANA MENÜ")
            print("  [1] Kitap Yönetimi")
            print("  [2] Üye Yönetimi")
            print("  [3] Ödünç İşlemleri")
            print("  [4] İstatistikler")
            print("  [0] Çıkış")
            print()

            choice = input("  Seçiminiz → ").strip()

            if choice == "1":
                books_menu(conn)
            elif choice == "2":
                members_menu(conn)
            elif choice == "3":
                borrow_menu(conn)
            elif choice == "4":
                statistics_menu(conn)
            elif choice == "0":
                d.info("Güle güle! 👋")
                break
            else:
                d.warning("Geçersiz seçim. Lütfen menüden bir numara girin.")

    except KeyboardInterrupt:
        print()
        d.info("Program sonlandırıldı (Ctrl+C).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
