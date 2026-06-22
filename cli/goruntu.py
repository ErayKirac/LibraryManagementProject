"""
cli/goruntu.py
--------------
Konsol çıktısı için ANSI renkli biçimlendirme yardımcıları.
Tablolar, başlıklar, uyarılar ve durum rozetleri burada tanımlanır.
"""

# ─── ANSI Renk Kodları ────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"

BLACK   = "\033[30m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
WHITE   = "\033[37m"

BG_BLUE    = "\033[44m"
BG_GREEN   = "\033[42m"
BG_RED     = "\033[41m"
BG_YELLOW  = "\033[43m"


# ─── Yardımcı Fonksiyonlar ────────────────────────────────────────────────────

def clr(text: str, color: str) -> str:
    """Verilen metni renklendirir."""
    return f"{color}{text}{RESET}"

def bold(text: str) -> str:
    return f"{BOLD}{text}{RESET}"

def success(msg: str) -> None:
    print(f"  {GREEN}✔{RESET}  {msg}")

def error(msg: str) -> None:
    print(f"  {RED}✘{RESET}  {msg}")

def warning(msg: str) -> None:
    print(f"  {YELLOW}⚠{RESET}  {msg}")

def info(msg: str) -> None:
    print(f"  {CYAN}ℹ{RESET}  {msg}")


def header(title: str) -> None:
    """Bölüm başlığı yazdırır."""
    width = 60
    print()
    print(f"{BOLD}{BLUE}{'─' * width}{RESET}")
    print(f"{BOLD}{BLUE}  {title.upper()}{RESET}")
    print(f"{BOLD}{BLUE}{'─' * width}{RESET}")


def banner() -> None:
    """Uygulama başlık ekranı."""
    print(f"""
{BOLD}{CYAN}
╔══════════════════════════════════════════════════════════╗
║         📚  KÜTÜPHANE YÖNETİM SİSTEMİ  📚              ║
║              Library Management System                   ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")


def status_badge(status: str) -> str:
    """Ödünç durumu için renkli rozet."""
    badges = {
        "borrowed": f"{YELLOW}[ÖDÜNÇte]{RESET}",
        "returned": f"{GREEN}[İADE]{RESET}   ",
        "overdue":  f"{RED}[GECİKMİŞ]{RESET}",
    }
    return badges.get(status, f"[{status}]")


def availability_badge(available: int, copies: int) -> str:
    """Kitap müsaitlik durumu rozeti."""
    if available == 0:
        return f"{RED}Mevcut yok{RESET}"
    ratio = available / copies
    color = GREEN if ratio > 0.5 else YELLOW
    return f"{color}{available}/{copies} kopya{RESET}"


# ─── Tablo Yazdırıcılar ───────────────────────────────────────────────────────

def print_books_table(books: list) -> None:
    """Kitap listesini tablo formatında yazdırır."""
    if not books:
        warning("Gösterilecek kitap bulunamadı.")
        return

    # Başlık satırı
    print(f"\n  {BOLD}{'ID':<5} {'ISBN':<16} {'Başlık':<30} {'Yazar':<22} {'Tür':<12} {'Yıl':<6} {'Durum':<16}{RESET}")
    print(f"  {'─'*5} {'─'*15} {'─'*29} {'─'*21} {'─'*11} {'─'*5} {'─'*15}")

    for b in books:
        avail = availability_badge(b["available"], b["copies"])
        title  = (b["title"][:27]  + "...") if len(b["title"])  > 30 else b["title"]
        author = (b["author"][:19] + "...") if len(b["author"]) > 22 else b["author"]
        year   = str(b["year"]) if b["year"] else "-"
        print(f"  {b['id']:<5} {b['isbn']:<16} {title:<30} {author:<22} {b['genre']:<12} {year:<6} {avail}")

    print(f"\n  Toplam: {bold(str(len(books)))} kitap\n")


def print_members_table(members: list) -> None:
    """Üye listesini tablo formatında yazdırır."""
    if not members:
        warning("Gösterilecek üye bulunamadı.")
        return

    print(f"\n  {BOLD}{'ID':<5} {'Ad Soyad':<25} {'E-posta':<30} {'Telefon':<16} {'Durum':<8}{RESET}")
    print(f"  {'─'*5} {'─'*24} {'─'*29} {'─'*15} {'─'*7}")

    for m in members:
        status_str = f"{GREEN}Aktif{RESET}  " if m["is_active"] else f"{RED}Pasif{RESET}  "
        name  = (m["name"][:22]  + "...") if len(m["name"])  > 25 else m["name"]
        email = (m["email"][:27] + "...") if len(m["email"]) > 30 else m["email"]
        phone = m["phone"] or "-"
        print(f"  {m['id']:<5} {name:<25} {email:<30} {phone:<16} {status_str}")

    print(f"\n  Toplam: {bold(str(len(members)))} üye\n")


def print_borrows_table(records: list, show_return: bool = False) -> None:
    """Ödünç kayıtları tablosunu yazdırır."""
    if not records:
        warning("Gösterilecek ödünç kaydı bulunamadı.")
        return

    if show_return:
        print(f"\n  {BOLD}{'ID':<5} {'Kitap':<28} {'Üye':<20} {'Alış':<12} {'İade tarihi':<12} {'Gerçek İade':<12} {'Durum':<13}{RESET}")
        print(f"  {'─'*5} {'─'*27} {'─'*19} {'─'*11} {'─'*11} {'─'*11} {'─'*12}")
    else:
        print(f"\n  {BOLD}{'ID':<5} {'Kitap':<28} {'Üye':<20} {'Alış':<12} {'Son Tarih':<12} {'Durum':<13}{RESET}")
        print(f"  {'─'*5} {'─'*27} {'─'*19} {'─'*11} {'─'*11} {'─'*12}")

    for r in records:
        title  = dict(r).get("title", "-")
        member = dict(r).get("member_name", dict(r).get("name", "-"))
        title  = (title[:25]  + "...") if len(title)  > 28 else title
        member = (member[:17] + "...") if len(member) > 20 else member
        badge  = status_badge(r["status"])

        if show_return:
            ret = r["return_date"] or "-"
            print(f"  {r['id']:<5} {title:<28} {member:<20} {r['borrow_date']:<12} {r['due_date']:<12} {ret:<12} {badge}")
        else:
            print(f"  {r['id']:<5} {title:<28} {member:<20} {r['borrow_date']:<12} {r['due_date']:<12} {badge}")

    print(f"\n  Toplam: {bold(str(len(records)))} kayıt\n")


def print_overdue_table(records: list) -> None:
    """Gecikmiş ödünç kayıtlarını yazdırır."""
    if not records:
        success("Gecikmiş ödünç kaydı bulunmuyor. 🎉")
        return

    print(f"\n  {BOLD}{'ID':<5} {'Kitap':<28} {'Üye':<20} {'Son Tarih':<12} {'Gecikme (gün)':<15}{RESET}")
    print(f"  {'─'*5} {'─'*27} {'─'*19} {'─'*11} {'─'*14}")

    for r in records:
        title  = r["title"]
        member = r["member_name"]
        title  = (title[:25]  + "...") if len(title)  > 28 else title
        member = (member[:17] + "...") if len(member) > 20 else member
        days   = int(r["overdue_days"]) if r["overdue_days"] else 0
        day_str = f"{RED}{days} gün{RESET}"
        print(f"  {r['id']:<5} {title:<28} {member:<20} {r['due_date']:<12} {day_str}")

    print(f"\n  {RED}{BOLD}⚠  {len(records)} gecikmiş kayıt bulunuyor!{RESET}\n")


def press_enter() -> None:
    """Kullanıcının Enter'a basmasını bekler."""
    input(f"  {BLUE}Menüye dönmek için Enter'a basın...{RESET}")


def separator() -> None:
    print(f"  {BLUE}{'·' * 56}{RESET}")
