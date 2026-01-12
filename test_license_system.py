"""
Test-Skript für Lizenz-System
Testet alle Funktionen des Lizenz-Systems
"""

from license_manager import LicenseManager
from colorama import Fore, init
import json

init(autoreset=True)

def test_db_connection():
    """Test 1: DB-Verbindung"""
    print(f"\n{Fore.CYAN}=== Test 1: DB-Verbindung ==={Fore.RESET}")
    
    lm = LicenseManager()
    conn = lm.connect_db()
    
    if conn:
        print(f"{Fore.GREEN}✓ DB-Verbindung erfolgreich!")
        conn.close()
        return True
    else:
        print(f"{Fore.RED}✗ DB-Verbindung fehlgeschlagen!")
        return False

def test_hardware_id():
    """Test 2: Hardware-ID"""
    print(f"\n{Fore.CYAN}=== Test 2: Hardware-ID ==={Fore.RESET}")
    
    lm = LicenseManager()
    print(f"Hardware-ID: {lm.hardware_id}")
    
    if lm.hardware_id and len(lm.hardware_id) > 0:
        print(f"{Fore.GREEN}✓ Hardware-ID generiert!")
        return True
    else:
        print(f"{Fore.RED}✗ Hardware-ID fehlt!")
        return False

def test_invalid_license():
    """Test 3: Ungültige Lizenz"""
    print(f"\n{Fore.CYAN}=== Test 3: Ungültige Lizenz ==={Fore.RESET}")
    
    lm = LicenseManager()
    valid, message = lm.check_license("INVALID-KEY-1234-5678", force_online=True)
    
    if not valid:
        print(f"{Fore.GREEN}✓ Ungültige Lizenz korrekt erkannt!")
        print(f"  Nachricht: {message}")
        return True
    else:
        print(f"{Fore.RED}✗ Ungültige Lizenz wurde akzeptiert!")
        return False

def test_valid_license():
    """Test 4: Gültige Lizenz (falls vorhanden)"""
    print(f"\n{Fore.CYAN}=== Test 4: Gültige Lizenz ==={Fore.RESET}")
    
    # Versuche Lizenz aus Cache zu laden
    lm = LicenseManager()
    cache = lm.load_license_cache()
    
    if not cache:
        print(f"{Fore.YELLOW}⚠ Kein Cache vorhanden - Test übersprungen")
        return True
    
    license_key = cache.get('license_key')
    if not license_key:
        print(f"{Fore.YELLOW}⚠ Kein Lizenzschlüssel im Cache - Test übersprungen")
        return True
    
    valid, message = lm.check_license(license_key, force_online=True)
    
    if valid:
        print(f"{Fore.GREEN}✓ Gültige Lizenz erkannt!")
        print(f"  Nachricht: {message}")
        return True
    else:
        print(f"{Fore.RED}✗ Gültige Lizenz wurde abgelehnt!")
        print(f"  Nachricht: {message}")
        return False

def test_cache_system():
    """Test 5: Cache-System"""
    print(f"\n{Fore.CYAN}=== Test 5: Cache-System ==={Fore.RESET}")
    
    lm = LicenseManager()
    
    # Lade Cache
    cache = lm.load_license_cache()
    
    if cache:
        print(f"{Fore.GREEN}✓ Cache geladen!")
        print(f"  Lizenzschlüssel: {cache.get('license_key', 'N/A')}")
        print(f"  Hardware-ID: {cache.get('hardware_id', 'N/A')}")
        print(f"  Gültig bis: {cache.get('valid_until', 'N/A')}")
        print(f"  Letzter Check: {cache.get('last_check', 'N/A')}")
        return True
    else:
        print(f"{Fore.YELLOW}⚠ Kein Cache vorhanden")
        return True

def test_offline_mode():
    """Test 6: Offline-Modus"""
    print(f"\n{Fore.CYAN}=== Test 6: Offline-Modus ==={Fore.RESET}")
    
    lm = LicenseManager()
    cache = lm.load_license_cache()
    
    if not cache:
        print(f"{Fore.YELLOW}⚠ Kein Cache vorhanden - Test übersprungen")
        return True
    
    # Prüfe ohne Online-Check (nutzt Cache)
    valid, message = lm.check_license(force_online=False)
    
    if valid:
        print(f"{Fore.GREEN}✓ Offline-Modus funktioniert!")
        print(f"  Nachricht: {message}")
        return True
    else:
        print(f"{Fore.RED}✗ Offline-Modus fehlgeschlagen!")
        print(f"  Nachricht: {message}")
        return False

def main():
    """Hauptfunktion"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"  Lizenz-System - Test-Suite")
    print(f"{'='*60}{Fore.RESET}\n")
    
    tests = [
        ("DB-Verbindung", test_db_connection),
        ("Hardware-ID", test_hardware_id),
        ("Ungültige Lizenz", test_invalid_license),
        ("Gültige Lizenz", test_valid_license),
        ("Cache-System", test_cache_system),
        ("Offline-Modus", test_offline_mode)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"{Fore.RED}✗ Fehler bei Test '{name}': {e}")
            results.append((name, False))
    
    # Zusammenfassung
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"  Zusammenfassung")
    print(f"{'='*60}{Fore.RESET}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Fore.GREEN}✓ PASS" if result else f"{Fore.RED}✗ FAIL"
        print(f"{status}{Fore.RESET} - {name}")
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"  Ergebnis: {passed}/{total} Tests bestanden")
    print(f"{'='*60}{Fore.RESET}\n")
    
    if passed == total:
        print(f"{Fore.GREEN}🎉 Alle Tests bestanden!{Fore.RESET}")
    else:
        print(f"{Fore.YELLOW}⚠ Einige Tests fehlgeschlagen!{Fore.RESET}")

if __name__ == '__main__':
    main()

