"""
Lizenz-Generator für Leitstellenspiel Bot
Erstellt neue Lizenzen in der Datenbank
"""

import json
import random
import string
import pymysql
from datetime import datetime, timedelta

def load_db_config():
    """Lädt DB-Konfiguration"""
    try:
        with open('db_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Fehler beim Laden der DB-Config: {e}")
        return None

def connect_db(config):
    """Verbindet zur Datenbank"""
    try:
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset=config['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"DB-Verbindung fehlgeschlagen: {e}")
        return None

def generate_license_key():
    """Generiert einen zufälligen Lizenzschlüssel"""
    # Format: XXXX-XXXX-XXXX-XXXX
    parts = []
    for _ in range(4):
        part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        parts.append(part)
    return '-'.join(parts)

def create_license(email, days_valid=365, notes=""):
    """Erstellt eine neue Lizenz"""
    config = load_db_config()
    if not config:
        return None
    
    conn = connect_db(config)
    if not conn:
        return None
    
    try:
        # Generiere Lizenzschlüssel
        license_key = generate_license_key()
        
        # Berechne Ablaufdatum
        expires_at = datetime.now() + timedelta(days=days_valid)
        
        # Füge in DB ein
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO licenses 
                (license_key, email, expires_at, is_active, notes) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (license_key, email, expires_at, True, notes))
            conn.commit()
        
        conn.close()
        
        print(f"✓ Lizenz erstellt!")
        print(f"  Lizenzschlüssel: {license_key}")
        print(f"  Email: {email}")
        print(f"  Gültig bis: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Notizen: {notes}")
        
        return license_key
        
    except Exception as e:
        print(f"Fehler beim Erstellen der Lizenz: {e}")
        return None

def list_licenses():
    """Listet alle Lizenzen auf"""
    config = load_db_config()
    if not config:
        return
    
    conn = connect_db(config)
    if not conn:
        return
    
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM licenses ORDER BY created_at DESC"
            cursor.execute(sql)
            results = cursor.fetchall()
            
            if not results:
                print("Keine Lizenzen gefunden.")
                return
            
            print(f"\n{'='*100}")
            print(f"{'ID':<5} {'Lizenzschlüssel':<25} {'Email':<30} {'Gültig bis':<20} {'Aktiv':<6}")
            print(f"{'='*100}")
            
            for row in results:
                license_id = row['id']
                license_key = row['license_key']
                email = row.get('email', 'N/A')
                expires_at = row.get('expires_at', 'Unbegrenzt')
                is_active = '✓' if row['is_active'] else '✗'
                
                if expires_at and expires_at != 'Unbegrenzt':
                    expires_at = expires_at.strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"{license_id:<5} {license_key:<25} {email:<30} {str(expires_at):<20} {is_active:<6}")
            
            print(f"{'='*100}\n")
        
        conn.close()
        
    except Exception as e:
        print(f"Fehler beim Auflisten der Lizenzen: {e}")

def main():
    """Hauptfunktion"""
    print("="*60)
    print("  Leitstellenspiel Bot - Lizenz-Generator")
    print("="*60)
    print()
    print("1. Neue Lizenz erstellen")
    print("2. Alle Lizenzen anzeigen")
    print("3. Beenden")
    print()
    
    choice = input("Wähle eine Option (1-3): ").strip()
    
    if choice == '1':
        print("\n--- Neue Lizenz erstellen ---")
        email = input("Email: ").strip()
        days_valid = input("Gültig für (Tage) [365]: ").strip()
        days_valid = int(days_valid) if days_valid else 365
        notes = input("Notizen (optional): ").strip()
        
        create_license(email, days_valid, notes)
    
    elif choice == '2':
        list_licenses()
    
    elif choice == '3':
        print("Auf Wiedersehen!")
    
    else:
        print("Ungültige Auswahl!")

if __name__ == '__main__':
    main()

