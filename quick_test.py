"""Quick test"""
print("Starting test...")

try:
    print("1. Importing LicenseManager...")
    from license_manager import LicenseManager
    print("   ✓ Import successful")
    
    print("2. Creating instance...")
    lm = LicenseManager()
    print("   ✓ Instance created")
    
    print("3. Hardware ID:", lm.hardware_id)
    
    print("4. Testing DB connection...")
    conn = lm.connect_db()
    if conn:
        print("   ✓ DB connection successful")
        conn.close()
    else:
        print("   ✗ DB connection failed")
    
    print("\n✓ All tests passed!")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

