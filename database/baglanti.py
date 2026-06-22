"""
database/baglanti.py
----------------------
SQLite veritabanı bağlantı yöneticisi.
Bağlantıyı açar, şemayı yükler ve temiz kapatma sağlar.
"""

import sqlite3
import os

# Proje kök dizinini ve yolları belirle
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH     = os.path.join(BASE_DIR, "library.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "sema.sql")


def get_connection() -> sqlite3.Connection:
    """
    Veritabanı bağlantısı döndürür.
    - Row factory: sütunlara isimle erişim sağlar (conn["title" gibi])
    - foreign_keys pragma: ON DELETE RESTRICT gibi kısıtlamaları etkinleştirir
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # Sonuçlara sözlük gibi erişim
    conn.execute("PRAGMA foreign_keys = ON") # Yabancı anahtar kısıtlamalarını aç
    return conn


def initialize_database() -> None:
    """
    Veritabanını ilk kez oluşturur ve örnek verileri yükler.
    Dosya zaten varsa yeniden oluşturmaz (INSERT OR IGNORE sayesinde).
    """
    conn = get_connection()
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            sql_script = f.read()
        conn.executescript(sql_script)
        conn.commit()
        print(f"[✔] Veritabanı hazır → {DB_PATH}")
    except FileNotFoundError:
        print(f"[!] Şema dosyası bulunamadı: {SCHEMA_PATH}")
    finally:
        conn.close()
